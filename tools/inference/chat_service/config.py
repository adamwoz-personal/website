"""Central config for the wosotowsky.org chat service.

All tunables live here so operators can find them in one place.
Environment variables override defaults for anything sensitive to deploy stage.
"""

from __future__ import annotations

import os
from pathlib import Path


AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")

MODEL_PRIMARY = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MODEL_FALLBACK = "amazon.nova-lite-v1:0"

MAX_INPUT_CHARS = 2000
MAX_OUTPUT_TOKENS = 600
MODEL_TEMPERATURE = 0.3

PER_IP_REQUESTS_PER_MINUTE = 5
PER_IP_REQUESTS_PER_HOUR = 30

DAILY_TOKEN_BUDGET_TOTAL = int(os.environ.get("CHAT_DAILY_TOKEN_BUDGET", "150000"))

BIND_HOST = os.environ.get("CHAT_BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("CHAT_BIND_PORT", "8787"))

STATE_DIR = Path(os.environ.get("CHAT_STATE_DIR", "/var/lib/wosotowsky-chat"))
USAGE_DB = STATE_DIR / "usage.sqlite"

DATA_DIR = Path(os.environ.get("CHAT_DATA_DIR", "/home/ec2-user/website/data"))
BIO_JSON = DATA_DIR / "bio" / "bio.json"
PATENTS_JSON = DATA_DIR / "patents" / "patents.json"
MENTIONS_JSON = DATA_DIR / "mentions" / "processed" / "classified.json"

_DEFAULT_IP_HASH_SALT = "wosotowsky-chat-dev-salt-change-me"
IP_HASH_SALT = os.environ.get("CHAT_IP_HASH_SALT", _DEFAULT_IP_HASH_SALT)
if IP_HASH_SALT == _DEFAULT_IP_HASH_SALT and str(STATE_DIR).startswith("/var/lib/"):
    raise RuntimeError("CHAT_IP_HASH_SALT must be set for production deployments")

LOG_LEVEL = os.environ.get("CHAT_LOG_LEVEL", "INFO")
