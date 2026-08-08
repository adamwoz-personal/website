# Content Routing Guide (Lessons Learned)

Durable decisions and pitfalls for the content-generation pipeline. Update this
file whenever a mistake is made twice.

---

## Operating instructions for AI assistants (READ FIRST)

This file exists so future assistants — including cheaper/less-capable
models — don't repeat mistakes we've already made. Follow the rules
below literally. If a rule below conflicts with your own inference,
**trust the rule**.

### Glossary (memorize these)

- **PR** = **Public Relations** in this project. Press interviews,
  quotes, features about Adam's cybersecurity work. Never GitHub pull
  requests.
- **Curated page** = `/adam/pr/`. Only URLs from popular US outlets in
  `POPULAR_US_DOMAINS`.
- **Broader sample page** = `/adam/mentions-all/`. Every verified mention
  regardless of language/region. Not exhaustive.
- **Verified** = the fetched page body contains "wosotowsky" (case
  insensitive) OR the URL is in the `trusted` list of `seeds.json`.
- **Trusted** = URLs the user vouches for that bot-block scrapers
  (IEEE, ResearchGate, Justia, ChabAD, Times of Malta, etc.).
- **Seeds** = the file `data/mentions/seeds.json`. Single source of truth
  for all press URLs.

### If you only remember five things

1. "PR" = Public Relations, not pull requests.
2. Never invent URLs. Only publish what the user gave you or what the
   verification gate approved.
3. Never call the mention lists complete. They are curated selections
   from hundreds. Always add `+` to visible tile counts.
4. **Site color palette is Georgia Tech-inspired: black + gold with
   navy and red accents.** Do not reintroduce pastel purple/pink/teal.
   CSS variables to use: `--gt-black`, `--gt-gold`, `--gt-gold-bright`,
   `--gt-navy`, `--gt-red`. Gradients: `--grad-gold`, `--grad-navy`,
   `--grad-red`.
5. **Static HTML preferred; light JS allowed.** Small vanilla JS is
   fine for chat widgets, dropdowns, etc. No frameworks, no CDN
   dependencies, no trackers.
5. Change page copy in `build_site.py`, not in the generated HTML.

### How this repo publishes content (canonical, do not deviate)

```
seeds.json (edit)                              <- your edits go here
  -> collect_mentions.py  (fetch + verify)
  -> classify_mentions.py (curated vs broader)
  -> fetch_patents.py     (with fallback)
  -> build_site.py        (render HTML)
  -> adam/                (generated HTML)     <- never hand-edit
  -> sudo cp -r adam /usr/share/nginx/html/adam
  -> sudo systemctl reload nginx
```

Orchestrator: `python3 tools/content_generation/run_pipeline.py`.

### Common mistakes previous assistants have made

1. Interpreted "PR" as GitHub pull requests and built the wrong page.
2. Added LLM-hallucinated URLs to seeds — most 404'd.
3. Hand-edited `adam/pr/index.html`, which was overwritten on next
   pipeline run.
4. Presented list counts as if they were Adam's total press coverage.
5. Added `<script>` tags for animations. Don't.
6. Passed AWS credentials on the command line. Use `aws configure`
   (already set up).
7. Modified `/usr/share/nginx/html/` directly instead of the repo.

If you catch yourself about to do any of the above: stop, re-read this
file, and use the workflow in `runbook.md` instead.

### When you're unsure, ask

Cheap models often make confident wrong changes. This project prefers
one clarifying question over three wrong commits. Ask the user rather
than guess site copy, curation criteria, or which URLs to add.

---

## Terminology

- **PR = Public Relations** in this project. It refers to press interviews,
  quotes, and features about Adam's cybersecurity work, primarily on
  popular US outlets. It does **not** refer to GitHub pull requests. Any
  future signal named "PR" must be interpreted this way.

## Routing defaults

1. Media/interview URLs live in `data/mentions/seeds.json` as human-curated
   seeds. Automated search-engine scraping is unreliable (Bing, DuckDuckGo,
   and Google all bot-block and/or ignore quoted phrases for rare surnames),
   so the pipeline is seed-driven, not crawler-driven.
2. Patent data comes from the Google Patents XHR endpoint, which is stable
   and returns clean JSON.
3. Scripts live in `tools/content_generation/`; intermediate data lives in
   `data/`; only reviewed static HTML is copied under `adam/` for the web
   root.

## Verification and trusted overrides

1. Every seeded URL under `seeds` is fetched. A mention is only surfaced on
   the site if the fetched HTML/PDF text actually contains one of the
   configured `match_terms` (default: `wosotowsky`). This eliminates common
   false positives such as:
   - Bible / religious references to the name "Adam"
   - Schools, businesses, and product names with "Adam" in them
   - Namesake pages of unrelated individuals
2. URLs the owner vouches for but that bot-block scrapers (IEEE Xplore,
   ResearchGate, Justia, ChabAD, Times of Malta, etc.) go in the `trusted`
   list of `seeds.json`. Trusted URLs are always published; the pipeline
   still records the fetch outcome for debugging.
3. Use the `titles` map in `seeds.json` to give trusted URLs a friendly
   display title (they usually can't be scraped for `<title>`).
4. Non-verified seeds are still recorded in `classified.json` under
   `unverified` for manual review, but never shown on the website.
5. PDFs are text-extracted via `pdftotext` (poppler-utils) before
   verification.

## Curation heuristics

1. Curated page ("Cybersecurity public relations") is restricted to a hard
   allow-list of popular US cybersecurity/technology outlets in
   `classify_mentions.py:POPULAR_US_DOMAINS` (Dark Reading, Threatpost,
   Wired, CNN, Reuters, PCWorld, PCMag, The Register, Softpedia,
   Infosecurity Magazine, McAfee, Trellix, etc.).
2. All other verified mentions (foreign-language outlets, small blogs,
   niche publications) go to the unabridged list.
3. To add or remove an outlet from the curated list, edit
   `POPULAR_US_DOMAINS` and re-run the pipeline.

## Editorial voice and framing

1. Adam has been quoted in hundreds of interviews and features across two
   decades. The published pages surface a **curated selection**, not the
   totality. Copy on the site must reflect that.
2. Never present the tile counts or list lengths as if they were the
   complete record. Prefer phrases like "a curated selection", "a broader
   sample", "highlighted from hundreds of..." and append a `+` to visible
   counts to convey open-endedness.
3. The "More verified mentions" page (route `/adam/mentions-all/`) is a
   working broader sample. It is intentionally not called "All mentions".
4. When adding new pages or copy, follow the same tone: understated,
   accurate about scope, and never implying finality.

## Security and reliability lessons

1. Static HTML is the default for pages under `adam/`. Small,
   purposeful JavaScript is permitted (chat widget, dropdown, copy
   button) as long as: no frameworks, no external CDNs, no trackers,
   and the JS stays small (a few KB per page). Keep the site low
   attack-surface. Never introduce a JS build pipeline or bundler.
2. `rel="noopener noreferrer"` on all outbound links.
3. `Referrer-Policy: no-referrer-when-downgrade` via meta tag.
4. Never publish `unverified` mentions - the "verified" gate is the whole
   point of the pipeline.
5. Search-engine scrapers should be treated as best-effort fallbacks only.
   Do not build critical pipelines that depend on Bing/DDG/Google HTML
   working; they will block automation.

## Common mistakes to avoid

1. Do not conflate "PR" with GitHub pull requests. This project's PR page
   is about media coverage.
2. Do not seed URLs without also updating `POPULAR_US_DOMAINS` if the
   outlet should appear on the curated page.
3. Do not publish LLM-provided URLs without letting `collect_mentions.py`
   verify them - LLMs commonly hallucinate URLs that 404.
4. Do not scrape Wayback CDX or Google Scholar in a tight loop; both will
   throttle and return HTML challenges.
5. Do not add hero content that requires a JS framework. Small vanilla
   JS is OK; do not introduce React/Vue/Svelte/etc.
6. Do not describe the mention lists as exhaustive. The curated page is a
   selection; the "more mentions" page is a broader sample; the archive
   itself spans hundreds of items and is not fully represented here.


## /adam/chat/ - public Q&A widget

Static page + external JS (`/adam/chat/chat.js`, same-origin, CSP-safe).
Widget POSTs to `/adam/chat/api/message`, which nginx proxies to a local
FastAPI service (see `docs/runbook.md`).

**AI-operator rules**:
- Chat widget JS lives at `adam/chat/chat.js` and is regenerated on any repo
  rebuild - do not edit the deployed copy on the box.
- Do not add inline `<script>` blocks to `/adam/chat/index.html`. Site CSP
  script-src is `'self'` with no unsafe-inline and no per-page hashes.
- Add new suggestion chips by editing `build_chat()` in
  `tools/content_generation/build_site.py`, NOT by editing the rendered HTML.
- The chat's model IDs and grounding context are set from
  `tools/inference/chat_service/config.py` and `context.py`, NOT from
  anywhere in this static site. Do not attempt to "improve the assistant"
  by editing the HTML.
