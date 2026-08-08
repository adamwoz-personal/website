#!/usr/bin/env python3
"""Fetch inventor patents from the Google Patents XHR endpoint.

Google Patents returns clean JSON for inventor-scoped queries. We store both
the raw response and a normalized record set for the site builder.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

from common import http_get


TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


@dataclass
class Patent:
    publication_number: str
    title: str
    snippet: str
    assignee: str
    filing_date: str
    grant_date: str
    priority_date: str
    inventor: str
    url: str


import html as html_lib


def clean(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html_lib.unescape(text)
    return WS_RE.sub(" ", text).strip()


def query_google_patents(inventor: str) -> dict:
    url = f"https://patents.google.com/xhr/query?url=inventor%3D%22{quote_plus(inventor)}%22&exp="
    status, body = http_get(url)
    if status != 200:
        raise RuntimeError(f"Google Patents returned status {status}")
    return json.loads(body)


def normalize(payload: dict) -> list[Patent]:
    patents: list[Patent] = []
    for cluster in payload.get("results", {}).get("cluster", []):
        for result in cluster.get("result", []):
            p = result.get("patent", {})
            pub = p.get("publication_number", "")
            patents.append(
                Patent(
                    publication_number=pub,
                    title=clean(p.get("title", "")),
                    snippet=clean(p.get("snippet", "")),
                    assignee=clean(p.get("assignee", "")),
                    filing_date=p.get("filing_date", ""),
                    grant_date=p.get("grant_date", ""),
                    priority_date=p.get("priority_date", ""),
                    inventor=clean(p.get("inventor", "")),
                    url=f"https://patents.google.com/patent/{pub}",
                )
            )
    return patents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch inventor patents from Google Patents.")
    parser.add_argument("--inventor", default="Adam Wosotowsky")
    parser.add_argument("--output", default="data/patents/patents.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    try:
        payload = query_google_patents(args.inventor)
        patents = normalize(payload)
    except Exception as exc:  # noqa: BLE001
        print(f"Live patent fetch failed ({exc}); keeping existing {output_path}", flush=True)
        if output_path.exists():
            return 0
        raise
    # Google Patents truncates titles/snippets with an ellipsis. If any
    # incoming record is truncated, prefer the hand-curated file on disk
    # so we don't overwrite good copy with truncated search-result text.
    def is_truncated(p) -> bool:
        joined = f"{p.title}\n{p.snippet}"
        return "\u2026" in joined or "..." in joined.rstrip(".")

    if output_path.exists() and any(is_truncated(p) for p in patents):
        print(
            f"Live patent fetch returned truncated fields; keeping existing "
            f"{output_path} to preserve curated titles.",
            flush=True,
        )
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "inventor": args.inventor,
                "count": len(patents),
                "patents": [asdict(p) for p in patents],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Fetched {len(patents)} patents for '{args.inventor}' -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
