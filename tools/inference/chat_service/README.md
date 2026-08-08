# wosotowsky.org public chat service

## READ FIRST — for AI operators and reviewers

This service is the **public-facing** RAG chat for `wosotowsky.org`. It answers
questions from anonymous visitors about Adam Wosotowsky, grounded in
`data/bio/bio.json`, `data/patents/patents.json`, and curated mentions.

Hard rules for anyone (human or AI) modifying this code:

1. **No AWS credentials on disk.** The service authenticates to Bedrock via the
   EC2 instance profile only. If you see `AWS_ACCESS_KEY_ID` / `aws_access_key_id`
   introduced anywhere, that is a bug. Reject it.
2. **All model IDs come from `config.py`.** Do not hardcode model IDs elsewhere.
   Haiku 4.5 must use the `us.` inference-profile prefix; direct model ID
   invocation is not supported by Bedrock for this model.
3. **Rate limits are load-bearing.** Do not remove or relax the per-IP and
   daily-token limits without also raising the CloudWatch billing alarm.
4. **The system prompt is a security boundary.** It instructs the model to
   refuse off-topic answers and to never reveal itself as an AI running on
   AWS Bedrock. Changes to the system prompt should be reviewed for prompt
   injection surface.
5. **SSE streaming is required** to keep first-byte latency low. Do not
   convert to buffered JSON responses.
6. **Log every request** to the local sqlite usage log. Costs must be
   auditable. Never PII-log (no message body storage beyond truncation for
   error triage, no raw IP addresses, only salted hash prefix).

## Architecture

```
Browser widget (/adam/chat/)
     |
     v POST /adam/chat/api/message (JSON)
Nginx (rate-limit zone `chat_zone`, TLS termination, forwards Real-IP)
     |
     v proxy_pass 127.0.0.1:8787
FastAPI (uvicorn, systemd-managed, User=chatapp)
     |
     v boto3 InvokeModelWithResponseStream (IAM instance profile)
Amazon Bedrock (us-east-2)
     - Primary: us.anthropic.claude-haiku-4-5-20251001-v1:0
     - Fallback: amazon.nova-lite-v1:0
```

## Files

- `app.py` — FastAPI app: `/message` (POST, SSE), `/health` (GET).
- `bedrock_client.py` — Streaming wrapper over boto3 with fallback logic.
- `context.py` — Loads bio + patents + curated mentions into a grounding
  context string. Regenerated on service start; caching handled by systemd.
- `system_prompt.py` — Renders the system prompt from context.
- `rate_limit.py` — Per-IP sliding window and daily global token budget.
- `usage_log.py` — Sqlite append-only usage log.
- `config.py` — All tunables in one place.
- `run.sh` — Local dev runner (does NOT run in prod; systemd does).

## Deploying

See `docs/runbook.md` — section "Chat service".
