#!/usr/bin/env python3
"""Fetch each seeded URL, verify the target name appears, and record metadata.

The output feeds classify_mentions.py and build_site.py. A mention is
"verified" if any of the following holds:
  1. The fetched HTML/PDF text actually contains one of the match_terms
     (default: "wosotowsky"). This prevents junk hits like Bible pages,
     elementary schools, or auto shops with unrelated "Adam" names.
  2. The URL is in the seed file's "trusted" list, meaning the site owner
     vouches for it (typically pages that bot-block scrapers such as
     IEEE, ResearchGate, ChabAD, Times of Malta, Justia, etc.).

Supports plain HTML pages and PDF documents (via pdftotext).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from common import DEFAULT_HEADERS, USER_AGENTS, http_get


@dataclass
class Mention:
    url: str
    domain: str
    status: int
    verified: bool
    trusted: bool
    title: str
    description: str
    match_terms_hit: list[str]
    content_type: str


META_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
META_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\']'
    r'[^>]*content=["\'](.*?)["\']',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


import html as html_lib


def clean(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = html_lib.unescape(text)
    return WS_RE.sub(" ", text).strip()


def extract_meta(html: str) -> tuple[str, str]:
    title_match = META_TITLE_RE.search(html)
    title = clean(title_match.group(1)) if title_match else ""
    desc_match = META_DESC_RE.search(html)
    description = clean(desc_match.group(1)) if desc_match else ""
    return title, description


def fetch_bytes(url: str, timeout: int = 30) -> tuple[int, bytes, str]:
    """Return (status, raw_bytes, content_type). Never raises."""
    for ua in USER_AGENTS:
        headers = {**DEFAULT_HEADERS, "User-Agent": ua}
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as response:
                raw = response.read()
                ct = response.headers.get("Content-Type", "").lower()
                return response.status, raw, ct
        except Exception:  # noqa: BLE001
            continue
    return 0, b"", ""


def pdf_text(raw: bytes) -> str:
    if not shutil.which("pdftotext"):
        return ""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", tmp_path, "-"],
            capture_output=True,
            timeout=60,
            check=False,
        )
        return result.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return ""
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def process(url: str, terms: list[str], trusted: bool = False) -> Mention:
    is_pdf_hint = url.lower().endswith(".pdf")
    if is_pdf_hint:
        status, raw, content_type = fetch_bytes(url)
        text = pdf_text(raw) if status == 200 else ""
        title = Path(urlparse(url).path).name
        description = "PDF document"
    else:
        status, body = http_get(url)
        content_type = "text/html"
        text = body
        title, description = extract_meta(body) if status == 200 else ("", "")
    text_lower = text.lower()
    hits = sorted({t for t in terms if t.lower() in text_lower})
    body_verified = status == 200 and bool(hits)
    return Mention(
        url=url,
        domain=urlparse(url).netloc.lower(),
        status=status,
        verified=body_verified or trusted,
        trusted=trusted,
        title=title,
        description=description,
        match_terms_hit=hits,
        content_type=content_type,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and verify seeded mention URLs.")
    parser.add_argument(
        "--seeds",
        default="data/mentions/seeds.json",
        help="Seed JSON file with a 'seeds' list and 'match_terms' list.",
    )
    parser.add_argument(
        "--output",
        default="data/mentions/raw/verified.json",
        help="Output JSON with per-URL verification metadata.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seed_path = Path(args.seeds)
    if not seed_path.exists():
        print(f"Seed file not found: {seed_path}", file=sys.stderr)
        return 2
    seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    seeds: list[str] = list(dict.fromkeys(seed_payload.get("seeds", [])))
    trusted_seeds: set[str] = set(seed_payload.get("trusted", []))
    all_urls = list(dict.fromkeys(seeds + list(trusted_seeds)))
    terms: list[str] = seed_payload.get("match_terms", ["wosotowsky"])

    results = [process(url, terms, trusted=(url in trusted_seeds)) for url in all_urls]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_source": str(seed_path),
        "match_terms": terms,
        "total_seeds": len(all_urls),
        "verified_count": sum(1 for r in results if r.verified),
        "trusted_count": sum(1 for r in results if r.trusted),
        "results": [asdict(r) for r in results],
    }
    output_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    print(
        f"Fetched {len(results)} seeds; verified={output_payload['verified_count']} "
        f"(of which {output_payload['trusted_count']} trusted); "
        f"output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())