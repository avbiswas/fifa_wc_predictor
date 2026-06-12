from __future__ import annotations

import json
from datetime import datetime, timezone

from .data import normalize_match_key
from .paths import PREDICTIONS_PATH, ROOT, STATIC_PREDICTIONS_PATH
from .goal_scorers import normalize_goal_scorers


def load_prediction_store() -> dict:
    if not PREDICTIONS_PATH.exists():
        return {"predictions": []}
    return json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))


def write_prediction_store(store: dict) -> None:
    content = json.dumps(store, indent=2, ensure_ascii=False) + "\n"
    for path in (PREDICTIONS_PATH, STATIC_PREDICTIONS_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def save_prediction_record(record: dict) -> str:
    store = load_prediction_store()
    record = {**record, "goal_scorers": normalize_goal_scorers(record.get("goal_scorers"))}
    stored_record = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "key": f"{normalize_match_key(record['match'])}::{record['model']}",
        **record,
    }
    store.setdefault("predictions", []).append(stored_record)
    write_prediction_store(store)
    return str(PREDICTIONS_PATH.relative_to(ROOT))
