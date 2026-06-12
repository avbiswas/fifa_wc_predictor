from __future__ import annotations

import argparse
import json

from .env import load_env
from .data import read_csv
from .paths import DATA_DIR
from .paths import PREDICTIONS_PATH, ROOT
from .predictions import load_prediction_store, write_prediction_store
from .results import fetch_match_result
from .scoring import score_store, update_leaderboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a completed World Cup result and score saved predictions.")
    parser.add_argument("--match-id", type=int, required=True)
    parser.add_argument("--fixture-id", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env()
    store = load_prediction_store()
    result = fetch_match_result(args.match_id, args.fixture_id)
    store.setdefault("results", {})[str(args.match_id)] = result
    store.setdefault("resolution_state", {}).setdefault("result_attempts", {}).pop(str(args.match_id), None)
    scored = score_store(store, args.match_id)
    update_leaderboard(store, read_csv(DATA_DIR / "schedule_2026.csv"))
    write_prediction_store(store)
    print(
        json.dumps(
            {
                "result": result,
                "predictions_scored": scored,
                "saved_to": str(PREDICTIONS_PATH.relative_to(ROOT)),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0
