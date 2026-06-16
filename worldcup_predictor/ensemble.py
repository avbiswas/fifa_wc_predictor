from __future__ import annotations

from collections import Counter, defaultdict
from math import ceil
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "min_matches_for_weight": 3,
    "min_coverage_ratio": 0.75,
    "top_models": 5,
    "weight_floor": 0.25,
    "draw_vote_threshold": 2,
    "draw_probability_floor": 0.20,
    "raw_draw_vote_threshold": 3,
    "raw_draw_share_floor": 0.20,
    "weak_favorite_probability_ceiling": 0.62,
    "low_confidence_ceiling": 0.62,
    "unanimous_low_confidence_ceiling": 0.68,
    "risk_confidence_penalty": 0.12,
    "min_models_for_action": 3,
}


def prediction_alias(prediction: dict) -> str:
    return prediction.get("model_alias") or prediction.get("model") or "unknown"


def latest_predictions(predictions: list[dict]) -> list[dict]:
    latest: dict[tuple[int, str], dict] = {}
    for prediction in predictions:
        if prediction.get("match_id") is None:
            continue
        key = (int(prediction["match_id"]), prediction_alias(prediction))
        previous = latest.get(key)
        if previous is None or prediction.get("created_at", "") >= previous.get("created_at", ""):
            latest[key] = prediction
    return list(latest.values())


def load_ensemble_config(path: Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path and path.exists():
        import json

        user_config = json.loads(path.read_text(encoding="utf-8"))
        for key, value in user_config.items():
            if key != "hermes_roster":
                config[key] = value
        config["hermes_roster"] = user_config.get("hermes_roster", [])
    return config


def build_model_weights(
    store: dict,
    config: dict[str, Any] | None = None,
    *,
    exclude_match_id: int | None = None,
) -> dict[str, Any]:
    config = {**DEFAULT_CONFIG, **(config or {})}
    completed_ids = {int(match_id) for match_id in store.get("results", {})}
    if exclude_match_id is not None:
        completed_ids.discard(int(exclude_match_id))

    grouped: dict[str, list[dict]] = defaultdict(list)
    for prediction in latest_predictions(store.get("predictions", [])):
        match_id = prediction.get("match_id")
        if match_id is None or int(match_id) not in completed_ids:
            continue
        if not prediction.get("score"):
            continue
        grouped[prediction_alias(prediction)].append(prediction)

    stats = []
    for alias, rows in grouped.items():
        total_points = sum(int(row.get("score", {}).get("total") or 0) for row in rows)
        correct_results = sum(1 for row in rows if int(row.get("score", {}).get("result") or 0) > 0)
        exact_scores = sum(1 for row in rows if int(row.get("score", {}).get("scoreline") or 0) > 0)
        matches = len(rows)
        stats.append(
            {
                "model_alias": alias,
                "matches": matches,
                "total_points": total_points,
                "average_points": total_points / matches if matches else 0.0,
                "correct_results": correct_results,
                "exact_scores": exact_scores,
            }
        )

    min_matches_floor = int(config.get("min_matches_for_weight", 3))
    required_matches = min_matches_floor
    if completed_ids:
        required_matches = max(
            min_matches_floor,
            ceil(len(completed_ids) * float(config.get("min_coverage_ratio", 0.75))),
        )
    eligible = [row for row in stats if row["matches"] >= required_matches]
    if not eligible:
        # If the result set has grown faster than model coverage, fall back to the
        # absolute sample floor — not to every one-match wonder at the top of the
        # leaderboard. Confetti is cute at parties, useless in model weighting.
        eligible = [row for row in stats if row["matches"] >= min_matches_floor]
        required_matches = min_matches_floor if eligible else required_matches
    if not eligible:
        eligible = [row for row in stats if row["matches"] > 0]
        required_matches = 1 if eligible else required_matches

    eligible.sort(
        key=lambda row: (
            -float(row["average_points"]),
            -int(row["correct_results"]),
            -int(row["exact_scores"]),
            str(row["model_alias"]),
        )
    )
    top_n = int(config.get("top_models", 5))
    selected = eligible[:top_n]
    best_average = max((float(row["average_points"]) for row in selected), default=0.0)
    floor = float(config.get("weight_floor", 0.25))
    models = []
    for row in selected:
        average = float(row["average_points"])
        weight = max(floor, average / best_average) if best_average else 1.0
        models.append({**row, "weight": round(weight, 4)})

    return {
        "models": models,
        "required_matches": required_matches,
        "completed_matches_used": len(completed_ids),
        "excluded_match_id": exclude_match_id,
    }


def model_weight_map(model_weights: dict[str, Any]) -> dict[str, float]:
    return {row["model_alias"]: float(row["weight"]) for row in model_weights.get("models", [])}


def _winner_from_counter(counter: Counter[str]) -> tuple[str | None, int]:
    if not counter:
        return None, 0
    winner, count = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0]
    return winner, count


def _winner_from_weights(weights: dict[str, float]) -> tuple[str | None, float]:
    if not weights:
        return None, 0.0
    winner, weight = sorted(weights.items(), key=lambda item: (-item[1], item[0]))[0]
    return winner, weight


def _average_confidence(predictions: list[dict]) -> float | None:
    values = []
    for prediction in predictions:
        try:
            values.append(float(prediction["confidence"]))
        except (KeyError, TypeError, ValueError):
            pass
    if not values:
        return None
    return sum(values) / len(values)


def forecast_match(
    predictions: list[dict],
    model_weights: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = {**DEFAULT_CONFIG, **(config or {})}
    latest = latest_predictions(predictions)
    if not latest:
        raise ValueError("forecast_match requires at least one prediction")

    weights = model_weight_map(model_weights)
    eligible = [prediction for prediction in latest if prediction_alias(prediction) in weights]
    if not eligible:
        eligible = latest
        weights = {prediction_alias(prediction): 1.0 for prediction in latest}

    raw_votes: Counter[str] = Counter()
    for prediction in latest:
        pick = prediction.get("prediction")
        if pick:
            raw_votes[str(pick)] += 1
    weighted_votes: dict[str, float] = defaultdict(float)
    for prediction in eligible:
        pick = prediction.get("prediction")
        if not pick:
            continue
        weighted_votes[str(pick)] += weights.get(prediction_alias(prediction), 1.0)

    raw_consensus, raw_votes_count = _winner_from_counter(raw_votes)
    weighted_consensus, weighted_total_for_pick = _winner_from_weights(weighted_votes)
    total_weight = sum(weighted_votes.values()) or 1.0
    raw_vote_total = sum(raw_votes.values()) or 1
    probabilities = {pick: round(weight / total_weight, 4) for pick, weight in sorted(weighted_votes.items())}
    weighted_probability = weighted_total_for_pick / total_weight if weighted_consensus else 0.0
    draw_probability = weighted_votes.get("Draw", 0.0) / total_weight
    draw_vote_count = sum(1 for prediction in eligible if prediction.get("prediction") == "Draw")
    raw_draw_vote_count = raw_votes.get("Draw", 0)
    raw_draw_share = raw_draw_vote_count / raw_vote_total
    average_confidence = _average_confidence(eligible)

    calibrated_pick = weighted_consensus or raw_consensus
    flags: list[str] = []
    if len(latest) < int(config.get("min_models_for_action", 3)):
        flags.append("insufficient_model_coverage")
    calibration_source = "weighted"
    if calibrated_pick != "Draw" and draw_vote_count >= int(config["draw_vote_threshold"]):
        if draw_probability >= float(config["draw_probability_floor"]):
            calibrated_pick = "Draw"
            flags.append("draw_calibration")
            calibration_source = "weighted_draw"
    if calibrated_pick != "Draw" and raw_draw_vote_count >= int(config["raw_draw_vote_threshold"]):
        if raw_draw_share >= float(config["raw_draw_share_floor"]):
            calibrated_pick = "Draw"
            flags.append("raw_draw_minority_calibration")
            calibration_source = "raw_draw_minority"

    if calibrated_pick != "Draw":
        if weighted_probability <= float(config["weak_favorite_probability_ceiling"]):
            flags.append("weak_favorite_signal")
        if average_confidence is not None and average_confidence <= float(config["low_confidence_ceiling"]):
            flags.append("low_model_confidence")
        if len(raw_votes) == 1 and average_confidence is not None:
            if average_confidence <= float(config["unanimous_low_confidence_ceiling"]):
                flags.append("unanimous_favorite_but_not_high_confidence")

    calibrated_probability = probabilities.get(calibrated_pick or "", 0.0)
    if calibration_source == "raw_draw_minority":
        calibrated_probability = max(calibrated_probability, raw_draw_share)
    if calibrated_pick != "Draw" and flags:
        calibrated_probability = max(0.0, calibrated_probability - float(config["risk_confidence_penalty"]))

    scoreline_pool = latest if calibration_source == "raw_draw_minority" else eligible
    scoreline_weights = weights | {prediction_alias(prediction): 1.0 for prediction in latest if prediction_alias(prediction) not in weights}
    scorer = select_scoreline_source(scoreline_pool, calibrated_pick, scoreline_weights)
    return {
        "raw_consensus": raw_consensus,
        "raw_votes": dict(sorted(raw_votes.items())),
        "raw_consensus_votes": raw_votes_count,
        "weighted_consensus": weighted_consensus,
        "weighted_probability": round(weighted_probability, 4),
        "weighted_probabilities": probabilities,
        "calibrated_pick": calibrated_pick,
        "calibrated_confidence": round(calibrated_probability, 4),
        "draw_vote_count": draw_vote_count,
        "draw_probability": round(draw_probability, 4),
        "raw_draw_vote_count": raw_draw_vote_count,
        "raw_draw_share": round(raw_draw_share, 4),
        "eligible_models": [prediction_alias(prediction) for prediction in eligible],
        "coverage": len(eligible),
        "average_model_confidence": round(average_confidence, 4) if average_confidence is not None else None,
        "risk_flags": flags,
        "scoreline": scorer.get("scoreline"),
        "scoreline_model_alias": prediction_alias(scorer) if scorer else None,
    }


def select_scoreline_source(predictions: list[dict], pick: str | None, weights: dict[str, float]) -> dict:
    if pick:
        matching = [prediction for prediction in predictions if prediction.get("prediction") == pick]
        if matching:
            return max(matching, key=lambda prediction: weights.get(prediction_alias(prediction), 1.0))
    return max(predictions, key=lambda prediction: weights.get(prediction_alias(prediction), 1.0))


def schedule_lookup(schedule: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    return {int(row["match_id"]): row for row in schedule if row.get("match_id")}


def match_name(match_id: int, schedule_by_id: dict[int, dict[str, str]], predictions: list[dict]) -> str:
    if match_id in schedule_by_id:
        row = schedule_by_id[match_id]
        return f"{row['team1']} vs {row['team2']}"
    for prediction in predictions:
        if int(prediction.get("match_id", -1)) == match_id:
            return prediction.get("match", f"match_id={match_id}")
    return f"match_id={match_id}"


def build_ensemble_report(
    store: dict,
    schedule: list[dict[str, str]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = {**DEFAULT_CONFIG, **(config or {})}
    schedule_by_id = schedule_lookup(schedule)
    latest = latest_predictions(store.get("predictions", []))
    predictions_by_match: dict[int, list[dict]] = defaultdict(list)
    for prediction in latest:
        if prediction.get("match_id") is not None:
            predictions_by_match[int(prediction["match_id"])].append(prediction)

    weights = build_model_weights(store, config)
    results = {int(match_id): result for match_id, result in store.get("results", {}).items()}
    backtest_rows = []
    forecast_rows = []

    for match_id in sorted(predictions_by_match):
        predictions = predictions_by_match[match_id]
        row_weights = build_model_weights(store, config, exclude_match_id=match_id) if match_id in results else weights
        forecast = forecast_match(predictions, row_weights, config)
        base = {
            "match_id": match_id,
            "match": match_name(match_id, schedule_by_id, predictions),
            "kickoff_utc": schedule_by_id.get(match_id, {}).get("kickoff_utc"),
            **forecast,
        }
        if match_id in results:
            actual = results[match_id]
            backtest_rows.append(
                {
                    **base,
                    "actual_winner": actual.get("winner"),
                    "actual_score": f"{actual.get('team1_score')}-{actual.get('team2_score')}",
                    "raw_correct": forecast["raw_consensus"] == actual.get("winner"),
                    "weighted_correct": forecast["weighted_consensus"] == actual.get("winner"),
                    "calibrated_correct": forecast["calibrated_pick"] == actual.get("winner"),
                }
            )
        else:
            forecast_rows.append(base)

    return {
        "config": config,
        "model_weights": weights,
        "backtest": summarize_backtest(backtest_rows),
        "backtest_rows": backtest_rows,
        "forecasts": forecast_rows,
    }


def summarize_backtest(rows: list[dict]) -> dict[str, Any]:
    total = len(rows)

    def count(field: str) -> int:
        return sum(1 for row in rows if row.get(field))

    return {
        "matches": total,
        "raw_consensus_correct": count("raw_correct"),
        "weighted_consensus_correct": count("weighted_correct"),
        "calibrated_correct": count("calibrated_correct"),
        "raw_consensus_rate": round(count("raw_correct") / total, 4) if total else 0.0,
        "weighted_consensus_rate": round(count("weighted_correct") / total, 4) if total else 0.0,
        "calibrated_rate": round(count("calibrated_correct") / total, 4) if total else 0.0,
    }
