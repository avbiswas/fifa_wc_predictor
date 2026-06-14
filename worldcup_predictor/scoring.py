from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from .goal_scorers import normalize_goal_scorers
from .models import load_model_registry


RESULT_POINTS = 50
SCORELINE_POINTS = 25
GOAL_DIFFERENCE_POINTS = 10
GOAL_SCORER_POINTS = 15


def score_prediction(prediction: dict, result: dict) -> dict:
    actual_score = (int(result["team1_score"]), int(result["team2_score"]))
    predicted_score = parse_scoreline(prediction.get("scoreline", ""))

    result_score = RESULT_POINTS if prediction.get("prediction") == result["winner"] else 0
    scoreline_score = score_scoreline(predicted_score, actual_score)
    goal_difference_score = score_goal_difference(predicted_score, actual_score)
    scorer_score, scorer_breakdown = score_goal_scorers(
        normalize_goal_scorers(prediction.get("goal_scorers")),
        result.get("goals", []),
    )
    return {
        "total": result_score + scoreline_score + goal_difference_score + scorer_score,
        "result": result_score,
        "scoreline": scoreline_score,
        "goal_difference": goal_difference_score,
        "goal_scorers": scorer_score,
        "goal_scorer_breakdown": scorer_breakdown,
    }


def score_store(store: dict, match_id: int | None = None) -> int:
    results = store.get("results", {})
    updated = 0
    for prediction in store.get("predictions", []):
        prediction_match_id = prediction.get("match_id")
        result = results.get(str(prediction_match_id)) if prediction_match_id is not None else None
        if result is None:
            result = next(
                (item for item in results.values() if item.get("match") == prediction.get("match")),
                None,
            )
        if result is None or (match_id is not None and int(result["match_id"]) != match_id):
            continue
        prediction["score"] = score_prediction(prediction, result)
        updated += 1
    return updated


def update_leaderboard(store: dict, schedule: list[dict]) -> dict:
    registry = load_model_registry()
    aliases_by_model = {
        value["model"] if isinstance(value, dict) else value: alias
        for alias, value in registry.get("models", {}).items()
    }
    latest_predictions: dict[tuple[int, str], dict] = {}
    latest: dict[tuple[int, str], dict] = {}
    for prediction in store.get("predictions", []):
        if prediction.get("match_id") is None:
            continue
        alias = prediction.get("model_alias") or aliases_by_model.get(prediction.get("model"))
        if not alias:
            continue
        key = (int(prediction["match_id"]), alias)
        latest_predictions[key] = prediction
        if prediction.get("score"):
            latest[key] = prediction

    aggregates = {alias: _empty_leaderboard_row(alias) for alias in registry.get("models", {})}
    for (_, alias), prediction in latest_predictions.items():
        row = aggregates.setdefault(alias, _empty_leaderboard_row(alias))
        row["total_cost"] += float(
            prediction.get("usage", {}).get("totals", {}).get("cost") or 0
        )
    for (_, alias), prediction in latest.items():
        row = aggregates.setdefault(alias, _empty_leaderboard_row(alias))
        score = prediction["score"]
        row["matches_scored"] += 1
        row["total_points"] += int(score["total"])
        row["result_points"] += int(score["result"])
        row["scoreline_points"] += int(score["scoreline"])
        row["goal_difference_points"] += int(score["goal_difference"])
        row["goal_scorer_points"] += int(score["goal_scorers"])
        row["correct_results"] += int(score["result"] == RESULT_POINTS)
        row["exact_scores"] += int(score["scoreline"] == SCORELINE_POINTS)
        row["correct_goal_scorers"] += int(score["goal_scorers"] / 5)

    rows = []
    for row in aggregates.values():
        matches = row["matches_scored"]
        row["average_points"] = round(row["total_points"] / matches, 2) if matches else 0
        row["total_cost"] = round(row["total_cost"], 8)
        rows.append(row)
    rows.sort(key=lambda row: (-row["total_points"], -row["average_points"], row["model_alias"]))

    schedule_by_id = {int(match["match_id"]): match for match in schedule}
    completed_matchdays = len(
        {
            schedule_by_id[int(match_id)].get("round")
            for match_id in store.get("results", {})
            if int(match_id) in schedule_by_id
        }
    )
    leaderboard = {
        "completed_matchdays": completed_matchdays,
        "available": bool(latest),
        "rows": rows,
    }
    previous = store.get("leaderboard", {})
    comparable_previous = {key: previous.get(key) for key in leaderboard}
    leaderboard["generated_at"] = (
        previous.get("generated_at")
        if comparable_previous == leaderboard and previous.get("generated_at")
        else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    store["leaderboard"] = leaderboard
    return leaderboard


def _empty_leaderboard_row(alias: str) -> dict:
    return {
        "model_alias": alias,
        "matches_scored": 0,
        "total_points": 0,
        "total_cost": 0.0,
        "result_points": 0,
        "scoreline_points": 0,
        "goal_difference_points": 0,
        "goal_scorer_points": 0,
        "correct_results": 0,
        "exact_scores": 0,
        "correct_goal_scorers": 0,
    }


def parse_scoreline(value: str) -> tuple[int, int] | None:
    match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", value)
    return (int(match.group(1)), int(match.group(2))) if match else None


def score_scoreline(predicted: tuple[int, int] | None, actual: tuple[int, int]) -> int:
    return SCORELINE_POINTS if predicted == actual else 0


def score_goal_difference(predicted: tuple[int, int] | None, actual: tuple[int, int]) -> int:
    if predicted is None:
        return 0
    return GOAL_DIFFERENCE_POINTS if predicted[0] - predicted[1] == actual[0] - actual[1] else 0


def score_goal_scorers(predicted: list[str], goals: list[dict]) -> tuple[int, list[dict]]:
    actual_scorers = [goal.get("scorer", "") for goal in goals if goal.get("scorer")]
    breakdown = []
    matched_actual: set[int] = set()
    for predicted_name in predicted[:3]:
        match_index = next(
            (
                index
                for index, actual_name in enumerate(actual_scorers)
                if index not in matched_actual and scorer_names_match(predicted_name, actual_name)
            ),
            None,
        )
        matched_name = actual_scorers[match_index] if match_index is not None else None
        if match_index is not None:
            matched_actual.add(match_index)
        breakdown.append(
            {
                "predicted": predicted_name,
                "matched_scorer": matched_name,
                "points": 5 if matched_name else 0,
            }
        )
    return min(GOAL_SCORER_POINTS, sum(item["points"] for item in breakdown)), breakdown


def scorer_names_match(predicted: str, actual: str) -> bool:
    predicted_tokens = _name_tokens(predicted)
    actual_tokens = _name_tokens(actual)
    if not predicted_tokens or not actual_tokens:
        return False
    if predicted_tokens == actual_tokens:
        return True

    actual_surname = actual_tokens[-1]
    actual_initials = [token[0] for token in actual_tokens[:-1] if token]
    orientations = [
        (predicted_tokens[-1], predicted_tokens[:-1]),
        (predicted_tokens[0], predicted_tokens[1:]),
    ]
    return any(
        surname == actual_surname
        and (
            not actual_initials
            or all(
                index < len(given_names) and given_names[index].startswith(initial)
                for index, initial in enumerate(actual_initials)
            )
        )
        for surname, given_names in orientations
    )


def _name_tokens(value: str) -> list[str]:
    value = value.split("(", 1)[0].strip()
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(character for character in normalized if character.isascii())
    return re.findall(r"[a-z]+", ascii_value.casefold())
