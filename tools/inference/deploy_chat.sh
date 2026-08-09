#!/usr/bin/env bash
# Deploy code updates to the chat service. Run on the EC2 instance from any directory.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
sudo rsync -a --delete --exclude '.git' --exclude '__pycache__' "$ROOT_DIR"/ /opt/wosotowsky-chat/website/
sudo chown -R chatapp:chatapp /opt/wosotowsky-chat/website
sudo systemctl restart wosotowsky-chat.service
sleep 2
curl -sS http://127.0.0.1:8787/health >/dev/null && echo "chat service healthy" || (echo "chat service unhealthy!" && sudo journalctl -u wosotowsky-chat -n 30 --no-pager && exit 1)
