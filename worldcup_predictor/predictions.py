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


def model_performance_context(
    store: dict,
    model_alias: str,
    model: str,
    current_match_id: int | None = None,
    limit: int = 5,
) -> str:
    rows = []
    results = store.get("results", {})
    for prediction in store.get("predictions", []):
        if prediction.get("model_alias") != model_alias and prediction.get("model") != model:
            continue
        match_id = prediction.get("match_id")
        if match_id is None or (current_match_id is not None and int(match_id) == current_match_id):
            continue
        result = results.get(str(match_id))
        score = prediction.get("score")
        if not result or not score:
            continue
        rows.append((prediction.get("created_at") or "", prediction, result, score))

    if not rows:
        return "Your last 5 match performances:\nNo scored match history available yet."

    lines = ["Your last 5 match performances:"]
    for index, (_, prediction, result, score) in enumerate(
        sorted(rows, key=lambda row: row[0], reverse=True)[:limit],
        start=1,
    ):
        winner = result.get("winner") or "Unknown"
        final_score = (
            f"{result.get('team1')} {result.get('team1_score')}-"
            f"{result.get('team2_score')} {result.get('team2')}"
        )
        lines.append(
            f"{index} | {prediction.get('match')} | "
            f"You predicted {prediction.get('scoreline')} | "
            f"Final score: {final_score} ({winner}) | "
            f"Your points: {score.get('total')}/100"
        )
    return "\n".join(lines)
