from __future__ import annotations

import argparse
import subprocess
import sys

from .data import get_match
from .models import competition_aliases
from .paths import ROOT
from .predictions import load_prediction_store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run only models missing a saved prediction for a match.")
    parser.add_argument("--match-id", type=int, default=1)
    parser.add_argument("--news-results", type=int, default=5)
    parser.add_argument("--skip-news", action="store_true")
    parser.add_argument("--skip-polymarket", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    store = load_prediction_store()
    match = get_match(args.match_id)
    match_name = f"{match['team1']} vs {match['team2']}"
    saved_aliases = {
        row.get("model_alias")
        for row in store.get("predictions", [])
        if row.get("match_id") == args.match_id
        or (row.get("match_id") is None and row.get("match") == match_name)
    }

    for alias in competition_aliases():
        if alias in saved_aliases:
            continue
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
        if args.skip_news:
            cmd.append("--skip-news")
        if args.skip_polymarket:
            cmd.append("--skip-polymarket")
        print(f"\n=== {alias} ===", flush=True)
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            print(f"Model failed: {alias}", file=sys.stderr)
    return 0
