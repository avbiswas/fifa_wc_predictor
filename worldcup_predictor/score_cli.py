from __future__ import annotations

import argparse
import json

from .data import read_csv
from .paths import DATA_DIR, PREDICTIONS_PATH, ROOT
from .predictions import load_prediction_store, write_prediction_store
from .scoring import score_store, update_leaderboard


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute prediction scores from saved match results.")
    parser.add_argument("--match-id", type=int)
    args = parser.parse_args()

    store = load_prediction_store()
    scored = score_store(store, args.match_id)
    update_leaderboard(store, read_csv(DATA_DIR / "schedule_2026.csv"))
    write_prediction_store(store)
    print(json.dumps({"predictions_scored": scored, "saved_to": str(PREDICTIONS_PATH.relative_to(ROOT))}))
    return 0
