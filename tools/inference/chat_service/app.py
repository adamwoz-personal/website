"""FastAPI app for the wosotowsky.org public chat.

Endpoints:
  GET  /health     - liveness + budget snapshot
  POST /message    - SSE stream of the model's reply

All errors return SSE `event: error` frames (never JSON in the middle of a stream).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from . import config
from .bedrock_client import stream as bedrock_stream
from .context import build_context
from .rate_limit import RateLimiter
from .system_prompt import render_system_prompt
from .usage_log import UsageLog


logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("chat")

app = FastAPI(title="wosotowsky-chat", docs_url=None, redoc_url=None, openapi_url=None)

_context_cache = build_context()
_system_prompt = render_system_prompt(_context_cache)
_rate = RateLimiter()
_usage = UsageLog()

log.info("context_bytes=%d system_prompt_bytes=%d", len(_context_cache), len(_system_prompt))


CTRL_CHARS = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")


def _client_ip(req: Request) -> str:
    xff = req.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return req.client.host if req.client else "0.0.0.0"


def _sse(event: str, data: str) -> bytes:
    payload = json.dumps({"data": data})
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "rate": _rate.snapshot(),
            "usage": _usage.summary(),
            "primary_model": config.MODEL_PRIMARY,
            "fallback_model": config.MODEL_FALLBACK,
        }
    )


@app.post("/message")
async def message(req: Request) -> StreamingResponse:
    started = time.monotonic()
    ip_raw = _client_ip(req)
    ip_hash = UsageLog.ip_hash(ip_raw)

    try:
        payload = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid_json"}, status_code=400)

    user_message = (payload.get("message") or "").strip()
    if not user_message:
        return JSONResponse({"error": "empty_message"}, status_code=400)
    if len(user_message) > config.MAX_INPUT_CHARS:
        return JSONResponse({"error": "message_too_long", "max": config.MAX_INPUT_CHARS}, status_code=400)
    if CTRL_CHARS.search(user_message):
        return JSONResponse({"error": "invalid_chars"}, status_code=400)

    ok, why = _rate.check_ip(ip_hash)
    if not ok:
        _usage.record(ip_hash=ip_hash, model=None, input_tokens=0, output_tokens=0, duration_ms=0, status="rejected", error_code=why, message=user_message)
        return JSONResponse({"error": why}, status_code=429)

    ok, why = _rate.check_budget()
    if not ok:
        _usage.record(ip_hash=ip_hash, model=None, input_tokens=0, output_tokens=0, duration_ms=0, status="rejected", error_code=why, message=user_message)
        return JSONResponse({"error": why}, status_code=503)

    async def gen():
        model_used: str | None = None
        input_tokens = 0
        output_tokens = 0

        from starlette.concurrency import iterate_in_threadpool

        try:
            async for model_id, chunk in iterate_in_threadpool(bedrock_stream(_system_prompt, user_message)):
                model_used = model_id
                if chunk.text:
                    yield _sse("token", chunk.text)
                if chunk.stop:
                    input_tokens = chunk.input_tokens or input_tokens
                    output_tokens = chunk.output_tokens or output_tokens
        except Exception:
            log.exception("bedrock stream failed")
            _usage.record(ip_hash=ip_hash, model=None, input_tokens=0, output_tokens=0, duration_ms=int((time.monotonic() - started) * 1000), status="error", error_code="bedrock_failed", message=user_message)
            yield _sse("error", "The assistant is unavailable right now. Please try again in a minute, or use the contact page.")
            return
        yield _sse("done", "")

        _rate.record_tokens(input_tokens + output_tokens)
        _usage.record(
            ip_hash=ip_hash,
            model=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=int((time.monotonic() - started) * 1000),
            status="ok",
            error_code=None,
            message=user_message,
        )

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
