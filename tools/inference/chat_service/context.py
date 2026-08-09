"""Builds the grounding context string used inside the system prompt.

We keep this compact: cheap-model context windows are big but every token
costs money. We aim for ~2-3k tokens of context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from . import config


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _bullets(items: Iterable[str], prefix: str = "- ") -> str:
    return "\n".join(f"{prefix}{s}" for s in items if s)


def build_context() -> str:
    bio = _load_json(config.BIO_JSON)
    patents = _load_json(config.PATENTS_JSON).get("patents", [])
    mentions = _load_json(config.MENTIONS_JSON).get("curated", [])

    parts: list[str] = []

    about = bio.get("about", {})
    parts.append("# About Adam Wosotowsky\n")
    parts.append(about.get("tagline", ""))
    parts.append("")
    for p in about.get("intro", []):
        parts.append(p)
    parts.append("")
    if about.get("highlights"):
        parts.append("Career highlights:")
        parts.append(_bullets(about["highlights"]))
        parts.append("")
    if about.get("roles_summary"):
        parts.append("Roles at a glance: " + about["roles_summary"])
        parts.append("")

    work = bio.get("work", {})
    if work.get("sections"):
        parts.append("# What Adam works on\n")
        parts.append(work.get("lead", ""))
        parts.append("")
        for s in work["sections"]:
            parts.append(f"## {s.get('heading','')}")
            for p in s.get("body", []):
                parts.append(p)
            parts.append("")

    if patents:
        parts.append("# Patents\n")
        for pat in patents:
            parts.append(f"- {pat.get('title','')} ({pat.get('id','')})")
            if pat.get("long_description"):
                parts.append(f"  {pat['long_description']}")
        parts.append("")

    if mentions:
        parts.append("# Selected public relations mentions\n")
        for m in mentions[:20]:
            title = m.get("title", "")
            outlet = m.get("outlet", "")
            year = m.get("year", "")
            parts.append(f"- {title} ({outlet}, {year})")
        parts.append("")

    philosophy = bio.get("philosophy", {})
    for essay in philosophy.get("essays", [])[:2]:
        parts.append(f"# Philosophy: {essay.get('heading','')}\n")
        for p in essay.get("body", [])[:4]:
            parts.append(p)
        parts.append("")

    speaking = bio.get("speaking", {})
    if speaking.get("sections"):
        parts.append("# Speaking and community\n")
        for s in speaking["sections"]:
            parts.append(f"- {s.get('heading','')}")
        parts.append("")

    lf = bio.get("looking_for", {})
    if lf.get("body"):
        parts.append("# What Adam is looking for\n")
        for p in lf["body"]:
            parts.append(p)
        parts.append("")

    contact = bio.get("contact", {})
    if contact.get("channels"):
        parts.append("# How to contact Adam")
        for ch in contact["channels"]:
            label = ch.get("label", "")
            value = ch.get("value", "")
            parts.append(f"- {label}: {value}")

    return "\n".join(parts).strip()
