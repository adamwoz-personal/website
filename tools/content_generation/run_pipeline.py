#!/usr/bin/env python3
"""Run the full content-generation pipeline end-to-end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run content pipeline.")
    parser.add_argument("--inventor", default="Adam Wosotowsky")
    parser.add_argument("--seeds", default="data/mentions/seeds.json")
    parser.add_argument("--skip-patents", action="store_true")
    parser.add_argument("--skip-mentions", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    py = sys.executable
    tool = "tools/content_generation"

    if not args.skip_mentions:
        run([py, f"{tool}/collect_mentions.py", "--seeds", args.seeds])
        run([py, f"{tool}/classify_mentions.py"])
    if not args.skip_patents:
        run([py, f"{tool}/fetch_patents.py", "--inventor", args.inventor])

    run([py, f"{tool}/build_site.py"])
    run([py, f"{tool}/build_assets.py"])
    run([py, f"{tool}/build_seo.py"])
    print("Pipeline completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
