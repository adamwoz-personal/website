"""Append-only sqlite usage log for auditability.

Never store raw IP, never store full message body. IP is stored as a salted
hash prefix (16 hex chars = 64 bits), message is stored as (length, first 64
chars) for triage of errors and abuse patterns.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import config


_SCHEMA = """
CREATE TABLE IF NOT EXISTS usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  ip_hash TEXT NOT NULL,
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  duration_ms INTEGER DEFAULT 0,
  status TEXT NOT NULL,
  error_code TEXT,
  message_len INTEGER,
  message_head TEXT
);
CREATE INDEX IF NOT EXISTS ix_usage_ts ON usage(ts);
CREATE INDEX IF NOT EXISTS ix_usage_status ON usage(status);
"""


class UsageLog:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or config.USAGE_DB
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as c:
            c.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, isolation_level=None, check_same_thread=False)

    @staticmethod
    def ip_hash(raw_ip: str) -> str:
        h = hashlib.sha256((config.IP_HASH_SALT + "|" + raw_ip).encode("utf-8")).hexdigest()
        return h[:16]

    def record(
        self,
        *,
        ip_hash: str,
        model: str | None,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        status: str,
        error_code: str | None,
        message: str,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        head = message[:64].replace("\n", " ").replace("\r", " ")
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO usage(ts, ip_hash, model, input_tokens, output_tokens, duration_ms, status, error_code, message_len, message_head) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (ts, ip_hash, model, input_tokens, output_tokens, duration_ms, status, error_code, len(message), head),
            )

    def summary(self) -> dict:
        with self._lock, self._connect() as c:
            row = c.execute("SELECT COUNT(*), COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0) FROM usage WHERE ts >= datetime('now','-24 hours')").fetchone()
