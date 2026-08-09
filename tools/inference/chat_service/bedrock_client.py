"""Streaming Bedrock client with primary + fallback.

Blocks a thread while it streams; call from a threadpool in the async app.
"""

from __future__ import annotations

import json
import logging
from typing import Iterator

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from . import config


log = logging.getLogger(__name__)


class StreamChunk:
    __slots__ = ("text", "input_tokens", "output_tokens", "stop")

    def __init__(self, text: str = "", input_tokens: int = 0, output_tokens: int = 0, stop: bool = False) -> None:
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.stop = stop


def _client():
    return boto3.client(
        "bedrock-runtime",
        region_name=config.AWS_REGION,
        config=BotoConfig(
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def _stream_claude(client, model_id: str, system: str, user: str) -> Iterator[StreamChunk]:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": config.MAX_OUTPUT_TOKENS,
        "temperature": config.MODEL_TEMPERATURE,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    resp = client.invoke_model_with_response_stream(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    input_tokens = 0
    output_tokens = 0
    for event in resp["body"]:
        chunk_raw = event.get("chunk", {}).get("bytes")
        if not chunk_raw:
            continue
        data = json.loads(chunk_raw)
        t = data.get("type")
        if t == "content_block_delta":
            delta = data.get("delta", {})
            if delta.get("type") == "text_delta":
                yield StreamChunk(text=delta.get("text", ""))
        elif t == "message_start":
            usage = data.get("message", {}).get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
        elif t == "message_delta":
            usage = data.get("usage", {})
            output_tokens = usage.get("output_tokens", output_tokens)
        elif t == "message_stop":
            yield StreamChunk(input_tokens=input_tokens, output_tokens=output_tokens, stop=True)


def _stream_nova(client, model_id: str, system: str, user: str) -> Iterator[StreamChunk]:
    body = {
        "system": [{"text": system}],
        "messages": [{"role": "user", "content": [{"text": user}]}],
        "inferenceConfig": {
            "maxTokens": config.MAX_OUTPUT_TOKENS,
            "temperature": config.MODEL_TEMPERATURE,
        },
    }
    resp = client.invoke_model_with_response_stream(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    input_tokens = 0
    output_tokens = 0
    for event in resp["body"]:
        chunk_raw = event.get("chunk", {}).get("bytes")
        if not chunk_raw:
            continue
        data = json.loads(chunk_raw)
        if "contentBlockDelta" in data:
            delta = data["contentBlockDelta"].get("delta", {})
            text = delta.get("text")
            if text:
                yield StreamChunk(text=text)
        elif "messageStop" in data:
            pass
        elif "metadata" in data:
            usage = data["metadata"].get("usage", {})
            input_tokens = usage.get("inputTokens", input_tokens)
            output_tokens = usage.get("outputTokens", output_tokens)
            yield StreamChunk(input_tokens=input_tokens, output_tokens=output_tokens, stop=True)


def stream(system: str, user: str) -> Iterator[tuple[str, StreamChunk]]:
    """Yields (model_id_used, chunk) tuples. Tries primary; falls back on ClientError."""
    client = _client()
    try:
        for c in _stream_claude(client, config.MODEL_PRIMARY, system, user):
            yield config.MODEL_PRIMARY, c
        return
    except ClientError as e:
        log.warning("primary model failed, falling back: %s", e)
    except Exception as e:
        log.exception("primary model failed with unexpected error: %s", e)

    for c in _stream_nova(client, config.MODEL_FALLBACK, system, user):
        yield config.MODEL_FALLBACK, c
