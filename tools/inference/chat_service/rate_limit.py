"""Per-IP sliding window and global daily token budget.

In-process only. If we ever scale beyond one uvicorn worker, move state into
sqlite or redis. For now a single-worker service is intentional and cheap.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from . import config


class RateLimiter:
    def __init__(self) -> None:
        self._minute: dict[str, deque[float]] = defaultdict(deque)
        self._hour: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._daily_tokens = 0
        self._daily_day = self._utc_day()

    @staticmethod
    def _utc_day() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _sweep(self, dq: deque[float], now: float, window: float) -> None:
        cutoff = now - window
        while dq and dq[0] < cutoff:
            dq.popleft()

    def check_ip(self, ip_key: str) -> tuple[bool, str]:
        now = time.monotonic()
        with self._lock:
            minute_dq = self._minute[ip_key]
            hour_dq = self._hour[ip_key]
            self._sweep(minute_dq, now, 60.0)
            self._sweep(hour_dq, now, 3600.0)
            if len(minute_dq) >= config.PER_IP_REQUESTS_PER_MINUTE:
                return False, "rate_limit_minute"
            if len(hour_dq) >= config.PER_IP_REQUESTS_PER_HOUR:
                return False, "rate_limit_hour"
            minute_dq.append(now)
            hour_dq.append(now)
        return True, ""

    def check_budget(self) -> tuple[bool, str]:
        with self._lock:
            today = self._utc_day()
            if today != self._daily_day:
                self._daily_day = today
                self._daily_tokens = 0
            if self._daily_tokens >= config.DAILY_TOKEN_BUDGET_TOTAL:
                return False, "daily_budget_exhausted"
        return True, ""

    def record_tokens(self, tokens: int) -> None:
        with self._lock:
            today = self._utc_day()
            if today != self._daily_day:
                self._daily_day = today
                self._daily_tokens = 0
            self._daily_tokens += max(0, tokens)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "daily_day": self._daily_day,
                "daily_tokens_used": self._daily_tokens,
                "daily_budget": config.DAILY_TOKEN_BUDGET_TOTAL,
                "active_ips_minute": len(self._minute),
                "active_ips_hour": len(self._hour),
            }
