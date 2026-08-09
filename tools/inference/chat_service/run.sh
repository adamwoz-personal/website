#!/usr/bin/env bash
# Local dev runner. Prod uses systemd (see docs/runbook.md).
set -euo pipefail
cd "$(dirname "$0")/../../.."
export AWS_REGION=${AWS_REGION:-us-east-2}
export CHAT_STATE_DIR=${CHAT_STATE_DIR:-/tmp/wosotowsky-chat-dev}
mkdir -p "$CHAT_STATE_DIR"
exec python3 -m uvicorn tools.inference.chat_service.app:app --host 127.0.0.1 --port 8787 --workers 1 "$@"
