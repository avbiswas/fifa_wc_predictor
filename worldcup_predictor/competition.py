from __future__ import annotations

import argparse
import subprocess
import sys

from .models import competition_aliases
from .paths import ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run predictions for every competition model.")
    parser.add_argument("--match-id", type=int, default=1)
    parser.add_argument("--news-results", type=int, default=5)
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--skip-news", action="store_true")
    parser.add_argument("--skip-polymarket", action="store_true")
    parser.add_argument("--start-at", help="Alias to start from when resuming a partial competition run.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    aliases = competition_aliases()
    if args.start_at:
        aliases = aliases[aliases.index(args.start_at) :]

    for alias in aliases:
        cmd = [
            sys.executable,
            "scripts/predict_match_dspy.py",
            "--match-id",
            str(args.match_id),
            "--model",
            alias,
            "--news-results",
            str(args.news_results),
        ]
        if args.refresh_cache:
            cmd.append("--refresh-cache")
        if args.skip_news:
            cmd.append("--skip-news")
        if args.skip_polymarket:
            cmd.append("--skip-polymarket")

        print(f"\n=== {alias} ===", flush=True)
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            print(f"Model failed: {alias}", file=sys.stderr)
    return 0
