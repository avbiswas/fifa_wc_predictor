#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.data import read_csv
from worldcup_predictor.paths import DATA_DIR, PREDICTIONS_PATH
from worldcup_predictor.predictions import load_prediction_store, write_prediction_store
from worldcup_predictor.scoring import parse_scoreline, score_store, update_leaderboard


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backtest saved World Cup predictions against fetched match results.")
    p.add_argument("--alias", action="append", help="Only include one model_alias. Repeatable.")
    p.add_argument("--latest-only", action="store_true", default=True, help="Use latest prediction per match/model alias.")
    p.add_argument("--all-predictions", action="store_false", dest="latest_only", help="Include duplicate historical predictions too.")
    p.add_argument("--json-out", default="reports/backtest_latest.json")
    p.add_argument("--markdown-out", default="reports/backtest_latest.md")
    p.add_argument("--no-write-scores", action="store_true")
    return p


def prediction_alias(prediction: dict) -> str:
    return prediction.get("model_alias") or prediction.get("model") or "unknown"


def latest_predictions(predictions: list[dict]) -> list[dict]:
    latest: dict[tuple[int, str], dict] = {}
    for pred in predictions:
        if pred.get("match_id") is None:
            continue
        key = (int(pred["match_id"]), prediction_alias(pred))
        previous = latest.get(key)
        if previous is None or pred.get("created_at", "") >= previous.get("created_at", ""):
            latest[key] = pred
    return list(latest.values())


def result_score(result: dict) -> str:
    return f"{result['team1']} {result['team1_score']}-{result['team2_score']} {result['team2']}"


def summarize(store: dict, aliases: set[str] | None, latest_only: bool) -> dict:
    results = {int(k): v for k, v in store.get("results", {}).items()}
    predictions = store.get("predictions", [])
    if latest_only:
        predictions = latest_predictions(predictions)
    if aliases:
        predictions = [p for p in predictions if prediction_alias(p) in aliases]

    rows = []
    by_alias: dict[str, dict] = {}
    by_match: dict[int, list[dict]] = defaultdict(list)

    for pred in predictions:
        match_id = pred.get("match_id")
        if match_id is None or int(match_id) not in results:
            continue
        result = results[int(match_id)]
        score = pred.get("score") or {}
        alias = prediction_alias(pred)
        predicted_score = parse_scoreline(pred.get("scoreline", ""))
        actual_score = (int(result["team1_score"]), int(result["team2_score"]))
        row = {
            "match_id": int(match_id),
            "match": result.get("match") or pred.get("match"),
            "actual": result_score(result),
            "actual_winner": result["winner"],
            "model_alias": alias,
            "prediction": pred.get("prediction"),
            "scoreline": pred.get("scoreline"),
            "confidence": pred.get("confidence"),
            "points": score.get("total"),
            "result_points": score.get("result"),
            "scoreline_points": score.get("scoreline"),
            "goal_difference_points": score.get("goal_difference"),
            "goal_scorer_points": score.get("goal_scorers"),
            "correct_result": pred.get("prediction") == result["winner"],
            "exact_score": predicted_score == actual_score,
            "created_at": pred.get("created_at"),
        }
        rows.append(row)
        by_match[int(match_id)].append(row)

    for alias in sorted({r["model_alias"] for r in rows}):
        alias_rows = [r for r in rows if r["model_alias"] == alias]
        n = len(alias_rows)
        total = sum(int(r["points"] or 0) for r in alias_rows)
        correct = sum(1 for r in alias_rows if r["correct_result"])
        exact = sum(1 for r in alias_rows if r["exact_score"])
        goal_diff = sum(1 for r in alias_rows if int(r["goal_difference_points"] or 0) > 0)
        scorer_points = sum(int(r["goal_scorer_points"] or 0) for r in alias_rows)
        by_alias[alias] = {
            "model_alias": alias,
            "matches": n,
            "total_points": total,
            "average_points": round(total / n, 2) if n else 0,
            "correct_results": correct,
            "correct_result_rate": round(correct / n, 3) if n else 0,
            "exact_scores": exact,
            "exact_score_rate": round(exact / n, 3) if n else 0,
            "goal_difference_hits": goal_diff,
            "goal_scorer_points": scorer_points,
        }

    consensus_rows = []
    for match_id, match_rows in sorted(by_match.items()):
        vote = Counter(r["prediction"] for r in match_rows)
        top_prediction, top_votes = vote.most_common(1)[0]
        result = results[match_id]
        consensus_rows.append({
            "match_id": match_id,
            "match": result.get("match"),
            "actual": result_score(result),
            "actual_winner": result["winner"],
            "consensus_prediction": top_prediction,
            "votes": top_votes,
            "models": len(match_rows),
            "correct_result": top_prediction == result["winner"],
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "completed_matches": [
            {
                "match_id": mid,
                "match": result.get("match"),
                "actual": result_score(result),
                "winner": result["winner"],
                "goals": result.get("goals", []),
            }
            for mid, result in sorted(results.items())
        ],
        "model_summary": sorted(by_alias.values(), key=lambda r: (-r["average_points"], -r["matches"], r["model_alias"])),
        "predictions": sorted(rows, key=lambda r: (r["match_id"], r["model_alias"])),
        "consensus": consensus_rows,
    }


def render_markdown(report: dict) -> str:
    lines = ["# FIFA WC Predictor backtest", "", f"Generated: `{report['generated_at']}`", ""]
    lines += ["## Completed matches", "", "| ID | Match | Actual | Winner |", "|---:|---|---|---|"]
    for row in report["completed_matches"]:
        lines.append(f"| {row['match_id']} | {row['match']} | {row['actual']} | {row['winner']} |")
    lines += ["", "## Model summary", "", "| Model | Matches | Avg pts | Total | Correct result | Exact score | GD hits | Scorer pts |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in report["model_summary"]:
        lines.append(
            f"| {row['model_alias']} | {row['matches']} | {row['average_points']} | {row['total_points']} | "
            f"{row['correct_results']}/{row['matches']} | {row['exact_scores']}/{row['matches']} | "
            f"{row['goal_difference_hits']} | {row['goal_scorer_points']} |"
        )
    lines += ["", "## Prediction rows", "", "| ID | Match | Actual | Model | Predicted | Scoreline | Pts |", "|---:|---|---|---|---|---|---:|"]
    for row in report["predictions"]:
        lines.append(
            f"| {row['match_id']} | {row['match']} | {row['actual']} | {row['model_alias']} | "
            f"{row['prediction']} | {row['scoreline']} | {row['points']} |"
        )
    lines += ["", "## Consensus", "", "| ID | Match | Actual | Consensus | Votes | Correct |", "|---:|---|---|---|---:|---|"]
    for row in report["consensus"]:
        lines.append(
            f"| {row['match_id']} | {row['match']} | {row['actual']} | {row['consensus_prediction']} | "
            f"{row['votes']}/{row['models']} | {row['correct_result']} |"
        )
    return "\n".join(lines) + "\n"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    args = build_parser().parse_args()
    store = load_prediction_store()
    scored = score_store(store)
    update_leaderboard(store, read_csv(DATA_DIR / "schedule_2026.csv"))
    if not args.no_write_scores:
        write_prediction_store(store)
    report = summarize(store, set(args.alias or []) or None, args.latest_only)

    json_path = ROOT / args.json_out
    md_path = ROOT / args.markdown_out
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(json.dumps({
        "completed_matches": len(report["completed_matches"]),
        "prediction_rows": len(report["predictions"]),
        "models": len(report["model_summary"]),
        "scores_recomputed": scored,
        "json_out": display_path(json_path),
        "markdown_out": display_path(md_path),
        "top_models": report["model_summary"][:5],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
