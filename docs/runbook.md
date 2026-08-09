# Content Generation Runbook

Reproducible pipeline that turns seed URLs and Google Patents data into the
static pages under `/adam`.

---

## Operating instructions for AI assistants (READ FIRST)

You are working on Adam Wosotowsky's personal website. Follow these rules
literally. When in doubt, do the smaller, safer thing and ask the user.

### Hard rules (never violate)

1. **"PR" means Public Relations.** It refers to press interviews, quotes,
   and features about Adam's cybersecurity work. It does **NOT** mean
   GitHub pull requests. If the user says "PR", assume media coverage.
2. **Never invent URLs.** Do not add URLs to `data/mentions/seeds.json`
   that you have not been given by the user or that the pipeline has not
   verified. LLM-suggested URLs are frequently hallucinated and will 404.
3. **Never claim a mention list is complete.** Adam has been quoted in
   hundreds of interviews. The site publishes only a curated selection.
   Copy must use words like "curated selection", "a broader sample",
   "highlighted from hundreds of..." Numeric counts on tiles must include
   a trailing `+` (e.g. `31+`).
4. **Static HTML preferred, light JS allowed.** Static HTML is still the
   default for anything under `adam/`. Small, purposeful JavaScript is OK
   (e.g. a chat widget, a lightweight dropdown, a copy-to-clipboard
   button) as long as: no frameworks, no external CDN dependencies, no
   trackers, and the JS is well under a few KB per page. When in doubt,
   don't add JS — but a single small script per page is not a policy
   violation.
5. **All outbound links** must include `rel="noopener noreferrer"`.
6. **Never publish `unverified` entries** from `classified.json`. If the
   user wants a bot-blocked page published, they will add it to the
   `trusted` list in `seeds.json`.
7. **Never commit secrets.** No AWS keys, tokens, or credentials in the
   repo. `aws configure` is already set up for the ec2-user; use the CLI
   without inline credentials.
8. **Never edit files under `/usr/share/nginx/html/` directly.** That
   directory is a *deploy target*. Edit files in `/home/ec2-user/website/`
   and re-run the deploy step.
9. **Do not rewrite git history** or force-push.

### The only workflow that publishes content

Any change to the visible site must go through this sequence:

```bash
cd /home/ec2-user/website

# 1. If adding press mentions, edit data/mentions/seeds.json only.
#    - Normal outlet -> append URL to "seeds".
#    - Bot-blocked outlet the user vouches for -> append URL to "trusted"
#      AND add a friendly title in "titles".

# 2. Rebuild everything (mentions, patents, HTML, favicon/OG card, robots+sitemap).
python3 tools/content_generation/run_pipeline.py

# 3. Deploy to nginx.
sudo rm -rf /usr/share/nginx/html/adam
sudo cp -r adam /usr/share/nginx/html/adam
sudo cp 404.html /usr/share/nginx/html/404.html
sudo cp robots.txt /usr/share/nginx/html/robots.txt
sudo cp sitemap.xml /usr/share/nginx/html/sitemap.xml
sudo systemctl reload nginx

# 4. Verify.
curl -sI https://wosotowsky.org/adam/pr/ | head -12   # expect HTTP/2 200 + security headers
curl -s -o /dev/null -w "%{http_code}\n" https://wosotowsky.org/adam/resume.pdf   # 200
curl -s -o /dev/null -w "%{http_code}\n" https://wosotowsky.org/nope              # 404
```

Never skip step 2. Never hand-edit generated files under `adam/` &mdash;
they are overwritten by `build_site.py`. If you need to change page
copy, edit `tools/content_generation/build_site.py` and re-run the
pipeline.

## Nginx security headers

Managed via `/etc/nginx/default.d/security-headers.conf`:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer-when-downgrade`
- `Content-Security-Policy` &mdash; self-only, no external scripts/styles/frames
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Permissions-Policy` &mdash; geolocation/microphone/camera denied

Do not relax the CSP to add a CDN or inline `<script>` without updating
this file first. The chat widget (when it lands) will be same-origin
only.

### Decision tree: "the user asked me to add a press mention"

1. Was I given a specific URL? If no, ask the user. Do not search the web
   and guess.
2. Does the URL exist? Fetch it once with `curl -sI` and confirm a 2xx or
   a known bot-challenge (403/202/503).
3. If 2xx and the page body contains "wosotowsky" (case-insensitive),
   append to `seeds` in `data/mentions/seeds.json`.
4. If the page bot-blocks scrapers but the user vouches for it, append to
   `trusted` and add a friendly title to `titles`.
5. Run the workflow above. Report the new counts.

### Decision tree: "the user asked me to change site copy"

1. Find the string in `tools/content_generation/build_site.py`. It is the
   only source of visible page copy for `/adam/*`.
2. Make the smallest edit that satisfies the request.
3. Do **not** change any of these framings without an explicit request:
   - Landing subhead mentioning "two decades" and "hundreds of press
     interviews".
   - PR page lead calling the list "a curated selection from hundreds".
   - "More verified mentions" page lead calling itself "a working subset".
   - Trailing `+` on tile counts.
4. Rebuild via `run_pipeline.py`. Deploy.

### Forbidden phrasings on the site

Do NOT introduce any of these on any page under `adam/`:

- "Complete list of..."
- "All mentions" as a *heading* (the route URL may stay for stability).
- Any number without a `+` on a landing-page tile.
- "Featured in over N publications" where N is the count of items on
  the page. Adam's real count is far higher.
- Any language implying the pipeline itself constitutes a portfolio
  audit.

### Preferred phrasings

- "A curated selection from hundreds of interviews..."
- "A broader sample across languages and regions..."
- "Highlighted from two decades of cybersecurity press..."
- "Working subset — not a comprehensive list."

### When you don't know what to do

Ask the user. Do not guess site copy, do not invent URLs, do not add new
scripts unless the user asks for them. Small clarifying questions are
always better than confident wrong output.

### Sanity checklist before saying "done"

- [ ] Did I edit `build_site.py` (not the generated HTML)?
- [ ] Did I run `python3 tools/content_generation/run_pipeline.py`?
- [ ] Did I `sudo cp -r adam /usr/share/nginx/html/adam` + reload nginx?
- [ ] Did `curl -sI https://wosotowsky.org/adam/` return 200?
- [ ] Did I update this runbook or the routing guide if I learned a new
  lesson worth remembering?

---

## Scope

- Scripts: `tools/content_generation/` (repo only; not served by nginx).
- Working data: `data/mentions/`, `data/patents/`.
- Published pages: `adam/index.html`, `adam/pr/`, `adam/mentions-all/`, `adam/patents/`.
- Web root default page (`index.html`) is unchanged by this pipeline.

## Quick start

From the repo root:

```bash
python3 tools/content_generation/run_pipeline.py
```

Then republish to the running nginx:

```bash
sudo rm -rf /usr/share/nginx/html/adam
sudo cp -r adam /usr/share/nginx/html/adam
sudo systemctl reload nginx
```

## Seed file structure (`data/mentions/seeds.json`)

Three lists, plus an optional titles map:

```json
{
  "match_terms": ["wosotowsky"],
  "seeds":   ["https://outlet.example/story"],
  "trusted": ["https://ieeexplore.ieee.org/document/123/"],
  "titles":  { "https://ieeexplore.ieee.org/document/123/": "Nice title" }
}
```

- **`seeds`** - fetched and only published if the fetched HTML/PDF actually
  contains one of `match_terms` (default: `wosotowsky`). This rejects
  namesake noise (Bible pages, schools, unrelated auto shops) and
  hallucinated URLs.
- **`trusted`** - always published; use this for pages the owner vouches
  for that bot-block scrapers (IEEE Xplore, ResearchGate, Justia,
  ChabAD, Times of Malta, etc.). The pipeline still records the fetch
  result for debugging.
- **`titles`** - optional per-URL display-title override, useful for
  trusted URLs where we can't scrape the HTML `<title>`.

## Adding a new press mention

1. Edit `data/mentions/seeds.json`:
   - Normal outlet -> append to `seeds`.
   - Bot-blocked outlet you can confirm manually -> append to `trusted`
     and add a friendly title in `titles`.
2. Re-run: `python3 tools/content_generation/run_pipeline.py`.
3. Redeploy nginx (`sudo cp -r adam ...`).

## Curated vs unabridged

- Curated ("Cybersecurity public relations") only includes verified mentions
  whose domain is in
  `tools/content_generation/classify_mentions.py:POPULAR_US_DOMAINS`.
- Unabridged ("All verified mentions") includes every verified mention
  regardless of language or region.

To add an outlet to the curated list, edit `POPULAR_US_DOMAINS`.

## Individual script usage

```bash
# 1. Fetch and verify seed URLs (HTML + PDF via pdftotext)
python3 tools/content_generation/collect_mentions.py \
  --seeds data/mentions/seeds.json \
  --output data/mentions/raw/verified.json

# 2. Split into curated / unabridged / unverified, apply title overrides
python3 tools/content_generation/classify_mentions.py \
  --input data/mentions/raw/verified.json \
  --seeds data/mentions/seeds.json \
  --output data/mentions/processed/classified.json

# 3. Pull patents from Google Patents (falls back to existing JSON on 5xx)
python3 tools/content_generation/fetch_patents.py \
  --inventor "Adam Wosotowsky" \
  --output data/patents/patents.json

# 4. Build /adam pages
python3 tools/content_generation/build_site.py \
  --mentions data/mentions/processed/classified.json \
  --patents data/patents/patents.json \
  --adam-dir adam
```

## Dependencies

- Python 3 stdlib only for the pipeline itself.
- `poppler-utils` (`pdftotext`) for PDF text extraction. Install on Amazon
  Linux 2023: `sudo dnf install -y poppler-utils`.

## Copy conventions

- Tile counts on the landing page use a trailing `+` (e.g. `31+`, `40+`)
  to indicate the archive is larger than what is currently published.
- The curated page is titled "Cybersecurity public relations" and its lead
  paragraph explicitly frames the list as a curated selection from
  hundreds of press interviews.
- The broader page is titled "More verified mentions" (route
  `/adam/mentions-all/` kept for URL stability). Its lead paragraph
  explicitly calls the list "a working subset ... not a comprehensive
  list."
- Landing hero includes a secondary lead (`p.lead-sub`) that establishes
  the "two decades / hundreds of press interviews" framing before any
  numeric tile is shown.
- When adding new seeds, do **not** change these framings to imply the
  new totals are exhaustive.

## Deployment notes

- Nginx document root is `/usr/share/nginx/html`.
- Only `index.html` and the `adam/` directory are copied to the web root.
- `tools/`, `data/`, and `docs/` are repo-only and never published.
- ALB `wosotowsky-web-alb` in `us-east-2` terminates TLS using ACM cert
  `arn:aws:acm:us-east-2:063330695683:certificate/7d777319-7900-4d2a-8976-c990e0188a19`.
- Route53 hosted zone `Z10313993OR8T9PIXA02E` has an A-alias for
  `wosotowsky.org.` pointing at the ALB.



---

## Chat service (added post-v0.1)

The public Q&A widget at `/adam/chat/` is powered by a small FastAPI service
running under systemd on the EC2 instance, calling AWS Bedrock via an IAM
instance profile.

**Components**:
- Code:               `tools/inference/chat_service/`
- systemd unit:       `tools/inference/wosotowsky-chat.service` (installed to `/etc/systemd/system/`)
- nginx rate zone:    `tools/inference/nginx-chat.conf` (installed as `/etc/nginx/conf.d/chat-zones.conf` and `/etc/nginx/default.d/chat.conf`)
- Deploy target:      `/opt/wosotowsky-chat/{website,venv}`
- Runtime state:      `/var/lib/wosotowsky-chat/usage.sqlite`
- Env file:           `/etc/wosotowsky-chat/env` (contains `CHAT_IP_HASH_SALT`, `CHAT_DAILY_TOKEN_BUDGET`, `CHAT_DATA_DIR`)
- User:               `chatapp` (system user, `/usr/sbin/nologin`)

**Redeploying code changes**:
```
cd /home/ec2-user/website
python3 tools/content_generation/run_pipeline.py         # static site
sudo tools/inference/deploy_chat.sh                       # syncs code + restarts service
sudo rm -rf /usr/share/nginx/html/adam && sudo cp -r adam /usr/share/nginx/html/adam
sudo cp {404.html,robots.txt,sitemap.xml} /usr/share/nginx/html/
sudo systemctl reload nginx
curl -sSf https://wosotowsky.org/adam/chat/ >/dev/null && echo OK
```

**Bedrock model IDs** (do not change without also updating the IAM policy at
`tools/inference/iam/bedrock-invoke-policy.json` and re-attaching):
- Primary:  `us.anthropic.claude-haiku-4-5-20251001-v1:0` (cross-region inference profile)
- Fallback: `amazon.nova-lite-v1:0`

Direct invocation of the base Haiku 4.5 model ID is not supported by Bedrock -
you must use the `us.` inference-profile prefix.

**Health, budget, and usage**:
```
curl -s http://127.0.0.1:8787/health | python3 -m json.tool
sudo sqlite3 /var/lib/wosotowsky-chat/usage.sqlite \
  "SELECT date(ts), model, count(*), sum(input_tokens), sum(output_tokens) FROM usage GROUP BY 1,2 ORDER BY 1 DESC LIMIT 14;"
```

**Rate limits**:
- Per-IP: 5 req/min, 30 req/hour (in-app)
- Per-IP: 30 req/min sustained + 10 burst (nginx `limit_req`)
- Global: `CHAT_DAILY_TOKEN_BUDGET` tokens/day (env, default 150k). When
  exhausted, the service returns HTTP 503 with `daily_budget_exhausted` until
  the next UTC midnight.

**AI-operator rules for this section**:
1. NEVER put AWS access keys in `/etc/wosotowsky-chat/env` or anywhere else on
   the box. The instance profile at `iam:role/wosotowsky-bedrock-role` provides
   credentials via IMDS. Adding keys is a regression.
2. If Bedrock model IDs change, update BOTH the app config AND
   `tools/inference/iam/bedrock-invoke-policy.json`, then re-attach the policy.
3. Do not disable the sandbox directives in the systemd unit (`ProtectSystem`,
   `NoNewPrivileges`, etc.) without a written justification.
4. Nginx location for `/adam/chat/api/message` MUST forward `X-Real-IP` so
   in-app rate limiting works correctly.
