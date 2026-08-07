#!/usr/bin/env python3
"""Split verified mentions into a curated US-popular list and an unabridged list.

Curated = pages on popular US-audience cybersecurity/tech outlets. Unabridged =
every verified mention regardless of outlet or language. Unverified fetches are
recorded separately for debugging.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

POPULAR_US_DOMAINS = {
    "abcnews.com": "ABC News",
    "abcnews.go.com": "ABC News",
    "archive.nytimes.com": "The New York Times (archive)",
    "arstechnica.com": "Ars Technica",
    "www.arstechnica.com": "Ars Technica",
    "www.asisonline.org": "ASIS Security Management",
    "asisonline.org": "ASIS Security Management",
    "www.bleepingcomputer.com": "BleepingComputer",
    "bleepingcomputer.com": "BleepingComputer",
    "www.cbc.ca": "CBC News",
    "cbc.ca": "CBC News",
    "www.chabad.org": "Chabad.org",
    "chabad.org": "Chabad.org",
    "www.cio.com": "CIO",
    "cio.com": "CIO",
    "www.cnet.com": "CNET",
    "cnet.com": "CNET",
    "www.cnn.com": "CNN",
    "cnn.com": "CNN",
    "www.cleveland.com": "Cleveland.com",
    "cleveland.com": "Cleveland.com",
    "www.computerweekly.com": "Computer Weekly",
    "computerweekly.com": "Computer Weekly",
    "www.crn.com": "CRN",
    "crn.com": "CRN",
    "www.csoonline.com": "CSO Online",
    "csoonline.com": "CSO Online",
    "www.darkreading.com": "Dark Reading",
    "darkreading.com": "Dark Reading",
    "www.databreachtoday.com": "Data Breach Today",
    "databreachtoday.com": "Data Breach Today",
    "dir.texas.gov": "Texas DIR",
    "www.eastbaytimes.com": "East Bay Times",
    "eastbaytimes.com": "East Bay Times",
    "www.forbes.com": "Forbes",
    "forbes.com": "Forbes",
    "www.foxbusiness.com": "Fox Business",
    "foxbusiness.com": "Fox Business",
    "www.govtech.com": "Government Technology",
    "govtech.com": "Government Technology",
    "www.helpnetsecurity.com": "Help Net Security",
    "helpnetsecurity.com": "Help Net Security",
    "ieeexplore.ieee.org": "IEEE Xplore",
    "www.infosecurity-magazine.com": "Infosecurity Magazine",
    "infosecurity-magazine.com": "Infosecurity Magazine",
    "krebsonsecurity.com": "Krebs on Security",
    "www.krebsonsecurity.com": "Krebs on Security",
    "www.kqed.org": "KQED",
    "kqed.org": "KQED",
    "www.latimes.com": "Los Angeles Times",
    "latimes.com": "Los Angeles Times",
    "www.mcafee.com": "McAfee",
    "mcafee.com": "McAfee",
    "www.mlive.com": "MLive",
    "mlive.com": "MLive",
    "www.nbcnews.com": "NBC News",
    "nbcnews.com": "NBC News",
    "www.nytimes.com": "The New York Times",
    "nytimes.com": "The New York Times",
    "patents.justia.com": "Justia Patents",
    "www.pcmag.com": "PCMag",
    "pcmag.com": "PCMag",
    "www.pcworld.com": "PCWorld",
    "pcworld.com": "PCWorld",
    "www.politifact.com": "PolitiFact",
    "politifact.com": "PolitiFact",
    "www.reuters.com": "Reuters",
    "reuters.com": "Reuters",
    "www.scmagazine.com": "SC Magazine",
    "scmagazine.com": "SC Magazine",
    "www.scworld.com": "SC World",
    "scworld.com": "SC World",
    "www.securityweek.com": "SecurityWeek",
    "securityweek.com": "SecurityWeek",
    "news.softpedia.com": "Softpedia News",
    "softpedia.com": "Softpedia News",
    "www.techradar.com": "TechRadar",
    "techradar.com": "TechRadar",
    "www.technewsworld.com": "TechNewsWorld",
    "technewsworld.com": "TechNewsWorld",
    "www.theregister.com": "The Register",
    "theregister.com": "The Register",
    "threatpost.com": "Threatpost",
    "www.threatpost.com": "Threatpost",
    "www.tomsguide.com": "Tom's Guide",
    "tomsguide.com": "Tom's Guide",
    "www.trellix.com": "Trellix",
    "trellix.com": "Trellix",
    "www.washingtonpost.com": "The Washington Post",
    "washingtonpost.com": "The Washington Post",
    "www.wired.com": "Wired",
    "wired.com": "Wired",
    "www.wsj.com": "The Wall Street Journal",
    "wsj.com": "The Wall Street Journal",
    "www.zimperium.com": "Zimperium",
    "zimperium.com": "Zimperium",
    "www.zdnet.com": "ZDNet",
    "zdnet.com": "ZDNet",
    "xcelevents.swoogo.com": "Texas DIR Info Security Forum",
}


def is_popular(domain: str) -> bool:
    return domain in POPULAR_US_DOMAINS


def outlet_name(domain: str) -> str:
    return POPULAR_US_DOMAINS.get(domain, domain)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify verified mentions.")
    parser.add_argument("--input", default="data/mentions/raw/verified.json")
    parser.add_argument("--seeds", default="data/mentions/seeds.json")
    parser.add_argument("--output", default="data/mentions/processed/classified.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    results = payload.get("results", [])

    title_overrides: dict[str, str] = {}
    seed_path = Path(args.seeds)
    if seed_path.exists():
        seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
        title_overrides = seed_payload.get("titles", {})

    curated: list[dict] = []
    unabridged: list[dict] = []
    unverified: list[dict] = []

    for r in results:
        r_out = dict(r)
        r_out["outlet"] = outlet_name(r.get("domain", ""))
        override = title_overrides.get(r.get("url", ""))
        if override:
            r_out["title"] = override
        if not r.get("verified"):
            unverified.append(r_out)
            continue
        unabridged.append(r_out)
        if is_popular(r.get("domain", "")):
            curated.append(r_out)

    def sort_key(item: dict) -> tuple[int, str]:
        return (0 if is_popular(item.get("domain", "")) else 1, item.get("title", ""))

    curated.sort(key=sort_key)
    unabridged.sort(key=sort_key)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input": args.input,
        "curated_count": len(curated),
        "unabridged_count": len(unabridged),
        "unverified_count": len(unverified),
        "curated": curated,
        "unabridged": unabridged,
        "unverified": unverified,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        f"Classified: curated={len(curated)}, unabridged={len(unabridged)}, "
        f"unverified={len(unverified)}; output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
