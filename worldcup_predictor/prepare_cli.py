from __future__ import annotations

import argparse
import json
from pathlib import Path

from .prepare import prepare_match_data, write_prepared_artifact
from .paths import ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare all local/retrieved artifacts for one match ID.")
    parser.add_argument("match_id", type=int)
    parser.add_argument("--news-results", type=int, default=5)
    parser.add_argument("--team1-record", default="Unavailable in local dataset for this prototype.")
    parser.add_argument("--team2-record", default="Unavailable in local dataset for this prototype.")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--skip-news", action="store_true")
    parser.add_argument("--skip-polymarket", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    artifact = prepare_match_data(
        match_id=args.match_id,
        news_results=args.news_results,
        team1_record=args.team1_record,
        team2_record=args.team2_record,
        refresh_cache=args.refresh_cache,
        skip_news=args.skip_news,
        skip_polymarket=args.skip_polymarket,
    )
    output_path = write_prepared_artifact(artifact, args.output)
    print(
        json.dumps(
            {
                "match": artifact["match"],
                "output": str(output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path),
                "cache": artifact["cache"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0
