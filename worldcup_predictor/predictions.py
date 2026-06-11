from __future__ import annotations

import json
from datetime import datetime, timezone

from .data import normalize_match_key
from .paths import PREDICTIONS_PATH, ROOT


def load_prediction_store() -> dict:
    if not PREDICTIONS_PATH.exists():
        return {"predictions": []}
    return json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))


def save_prediction_record(record: dict) -> str:
    store = load_prediction_store()
    stored_record = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "key": f"{normalize_match_key(record['match'])}::{record['model']}",
        **record,
    }
    store.setdefault("predictions", []).append(stored_record)
    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(PREDICTIONS_PATH.relative_to(ROOT))
