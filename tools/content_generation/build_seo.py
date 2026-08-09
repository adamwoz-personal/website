#!/usr/bin/env python3
"""Generate sitemap.xml and robots.txt at the web root of the repo."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


PAGES = [
    "/",
    "/adam/",
    "/adam/about/",
    "/adam/work/",
    "/adam/philosophy/",
    "/adam/speaking/",
    "/adam/pr/",
    "/adam/patents/",
    "/adam/mentions-all/",
    "/adam/chat/",
    "/adam/contact/",
]


def build_sitemap(base_url: str, pages: list[str]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = "\n".join(
        f"  <url>\n    <loc>{base_url}{p}</loc>\n    <lastmod>{today}</lastmod>\n  </url>"
        for p in pages
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )


ROBOTS = """User-agent: *
Allow: /
Disallow: /api/

Sitemap: https://wosotowsky.org/sitemap.xml
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate robots.txt and sitemap.xml.")
    parser.add_argument("--base-url", default="https://wosotowsky.org")
    parser.add_argument("--out", default=".", help="output directory")
    args = parser.parse_args()
    out = Path(args.out)
    (out / "sitemap.xml").write_text(build_sitemap(args.base_url, PAGES), encoding="utf-8")
    (out / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    print(f"Wrote sitemap.xml and robots.txt in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
