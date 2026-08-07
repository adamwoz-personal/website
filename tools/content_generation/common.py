"""Shared helpers for the content-generation pipeline."""

from __future__ import annotations

import gzip
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENTS = [
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 "
        "Firefox/127.0"
    ),
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Connection": "close",
}


def _decode(response, raw: bytes) -> str:
    if response.headers.get("Content-Encoding", "").lower() == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def http_get(url: str, timeout: int = 25, retries: int = 3) -> tuple[int, str]:
    """Return (status_code, body_text). Retries with rotating User-Agents.

    Never raises for HTTP or network errors; returns status=0 for connect
    failures and includes a short reason in the body for logging.
    """
    last_status = 0
    last_body = ""
    for attempt in range(retries):
        ua = USER_AGENTS[attempt % len(USER_AGENTS)]
        headers = {**DEFAULT_HEADERS, "User-Agent": ua}
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=timeout) as response:
                body = _decode(response, response.read())
                return response.status, body
        except HTTPError as exc:
            try:
                body = _decode(exc, exc.read() or b"")
            except Exception:
                body = ""
            last_status, last_body = exc.code, body
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(1 + attempt)
                continue
            return exc.code, body
        except URLError as exc:
            last_status, last_body = 0, f"URLError: {exc.reason}"
            time.sleep(1 + attempt)
        except Exception as exc:  # noqa: BLE001
            last_status, last_body = 0, f"Exception: {exc}"
            time.sleep(1 + attempt)
    return last_status, last_body
