from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from .data import read_csv
from .env import load_env
from .models import competition_aliases, load_model_registry
from .paths import DATA_DIR, ROOT
from .predictions import load_prediction_store, write_prediction_store
from .results import fetch_match_result
from .scoring import score_store, update_leaderboard


RESULT_RETRY_DELAY = timedelta(hours=1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve predictions, results, scores, and leaderboard for the day.")
    parser.add_argument("--now", help="Override current time with an ISO-8601 timestamp for testing.")
    parser.add_argument("--dry-run", action="store_true", help="Print work without running models or APIs.")
    parser.add_argument("--news-results", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env()
    now = parse_now(args.now)
    schedule = read_csv(DATA_DIR / "schedule_2026.csv")
    store = load_prediction_store()

    plan = resolve_day(store, schedule, now, args.news_results, dry_run=True)
    print("Planned work:")
    print(json.dumps(format_plan(plan), indent=2, ensure_ascii=False))
    if args.dry_run:
        return 0

    fetch_results = False
    if plan["results_fetched"]:
        confirmation = input(
            f"\nFetch all {len(plan['results_fetched'])} pending past match result(s)? Type Y to continue: "
        ).strip()
        fetch_results = confirmation.casefold() == "y"

    selected_prediction_match_ids = []
    for item in plan["predictions_run"]:
        confirmation = input(
            f"Run {len(item['models'])} missing model prediction(s) for "
            f"{item['match']} [match {item['match_number']}]? Type Y to continue: "
        ).strip()
        if confirmation.casefold() == "y":
            selected_prediction_match_ids.append(int(item["match_id"]))

    if not fetch_results and not selected_prediction_match_ids:
        print("Nothing approved. No model or result API calls were made.")
        return 0

    summary = resolve_day(
        store,
        schedule,
        now,
        args.news_results,
        dry_run=False,
        selected_prediction_match_ids=set(selected_prediction_match_ids),
        fetch_results=fetch_results,
    )
    print("\nCompleted work:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return int(bool(summary["prediction_failures"] or summary["result_failures"]))


def resolve_day(
    store: dict,
    schedule: list[dict],
    now: datetime,
    news_results: int,
    dry_run: bool,
    selected_prediction_match_ids: set[int] | None = None,
    fetch_results: bool = True,
) -> dict:
    initial_store = json.dumps(store, sort_keys=True, ensure_ascii=False)
    match_numbers = chronological_match_numbers(schedule)
    prediction_matches = matches_in_prediction_window(schedule, now)
    result_matches = unresolved_past_matches(store, schedule, now)
    if not dry_run and selected_prediction_match_ids is not None:
        prediction_matches = [
            match for match in prediction_matches if int(match["match_id"]) in selected_prediction_match_ids
        ]
    if not dry_run and not fetch_results:
        result_matches = []
    summary = {
        "resolved_at": now.isoformat().replace("+00:00", "Z"),
        "dry_run": dry_run,
        "prediction_window_match_ids": [int(match["match_id"]) for match in prediction_matches],
        "result_candidate_match_ids": [int(match["match_id"]) for match in result_matches],
        "predictions_run": [],
        "predictions_skipped": [],
        "prediction_failures": [],
        "results_fetched": [],
        "results_skipped": [],
        "result_failures": [],
    }
    predictions_changed = False

    for match in prediction_matches:
        match_id = int(match["match_id"])
        missing = missing_prediction_aliases(store, match_id, match)
        if not missing:
            summary["predictions_skipped"].append(
                {
                    "match_id": match_id,
                    "match_number": match_numbers[match_id],
                    "reason": "complete",
                }
            )
            continue
        if dry_run:
            summary["predictions_run"].append(
                {
                    "match_id": match_id,
                    "match_number": match_numbers[match_id],
                    "match": f"{match['team1']} vs {match['team2']}",
                    "models": missing,
                }
            )
            continue
        for alias in missing:
            command = [
                sys.executable,
                "scripts/predict_match_dspy.py",
                "--match-id",
                str(match_id),
                "--model",
                alias,
                "--news-results",
                str(news_results),
            ]
            result = subprocess.run(command, cwd=ROOT)
            if result.returncode == 0:
                predictions_changed = True
                summary["predictions_run"].append({"match_id": match_id, "model": alias})
            else:
                summary["prediction_failures"].append({"match_id": match_id, "model": alias})

    if predictions_changed:
        store = load_prediction_store()

    for match in result_matches:
        match_id = int(match["match_id"])
        if result_retry_pending(store, match_id, now):
            summary["results_skipped"].append(
                {
                    "match_id": match_id,
                    "match_number": match_numbers[match_id],
                    "reason": "retry pending",
                }
            )
            continue
        if dry_run:
            summary["results_fetched"].append(
                {
                    "match_id": match_id,
                    "match_number": match_numbers[match_id],
                    "match": f"{match['team1']} vs {match['team2']}",
                }
            )
            continue
        try:
            result = fetch_match_result(match_id)
        except (SystemExit, Exception) as error:
            message = str(error)
            store.setdefault("resolution_state", {}).setdefault("result_attempts", {})[str(match_id)] = {
                "checked_at": now.isoformat().replace("+00:00", "Z"),
                "retry_after": (now + RESULT_RETRY_DELAY).isoformat().replace("+00:00", "Z"),
                "error": message,
            }
            summary["result_failures"].append({"match_id": match_id, "error": message})
            write_prediction_store(store)
            continue
        store.setdefault("results", {})[str(match_id)] = result
        store.setdefault("resolution_state", {}).setdefault("result_attempts", {}).pop(str(match_id), None)
        summary["results_fetched"].append({"match_id": match_id, "fixture_id": result["fixture_id"]})
        write_prediction_store(store)

    if not dry_run:
        score_store(store)
        leaderboard = update_leaderboard(store, schedule)
        if json.dumps(store, sort_keys=True, ensure_ascii=False) != initial_store:
            write_prediction_store(store)
        summary["leaderboard"] = {
            "completed_matchdays": leaderboard["completed_matchdays"],
            "available": leaderboard["available"],
        }
    return summary


def format_plan(summary: dict) -> dict:
    return {
        "resolved_at": summary["resolved_at"],
        "predictions_to_run": [_public_action(item) for item in summary["predictions_run"]],
        "predictions_already_complete": [_public_action(item) for item in summary["predictions_skipped"]],
        "results_to_fetch": [_public_action(item) for item in summary["results_fetched"]],
        "results_waiting_for_retry": [_public_action(item) for item in summary["results_skipped"]],
    }


def _public_action(item: dict) -> dict:
    return {
        "match_number": item.get("match_number"),
        **{key: value for key, value in item.items() if key not in {"match_id", "match_number"}},
    }


def matches_in_prediction_window(schedule: list[dict], now: datetime) -> list[dict]:
    window_end = now + timedelta(hours=24)
    return [
        match
        for match in schedule
        if now < kickoff(match) <= window_end and is_resolved_fixture(match)
    ]


def chronological_match_numbers(schedule: list[dict]) -> dict[int, int]:
    ordered = sorted(schedule, key=lambda match: (kickoff(match), int(match["match_id"])))
    return {
        int(match["match_id"]): index
        for index, match in enumerate(ordered, start=1)
    }


def unresolved_past_matches(store: dict, schedule: list[dict], now: datetime) -> list[dict]:
    resolved_ids = {int(match_id) for match_id in store.get("results", {})}
    return [
        match
        for match in schedule
        if kickoff(match) <= now and int(match["match_id"]) not in resolved_ids and is_resolved_fixture(match)
    ]


def missing_prediction_aliases(store: dict, match_id: int, match: dict) -> list[str]:
    registry = load_model_registry()
    aliases_by_model = {
        value["model"] if isinstance(value, dict) else value: alias
        for alias, value in registry.get("models", {}).items()
    }
    match_name = f"{match['team1']} vs {match['team2']}"
    saved = {
        row.get("model_alias") or aliases_by_model.get(row.get("model"))
        for row in store.get("predictions", [])
        if row.get("match_id") == match_id or (row.get("match_id") is None and row.get("match") == match_name)
    }
    return [alias for alias in competition_aliases() if alias not in saved]


def result_retry_pending(store: dict, match_id: int, now: datetime) -> bool:
    attempt = store.get("resolution_state", {}).get("result_attempts", {}).get(str(match_id))
    if not attempt or not attempt.get("retry_after"):
        return False
    if "API-Football" in attempt.get("error", ""):
        return False
    return parse_now(attempt["retry_after"]) > now


def kickoff(match: dict) -> datetime:
    return parse_now(match["kickoff_utc"])


def is_resolved_fixture(match: dict) -> bool:
    return bool(match.get("team1_code") and match.get("team2_code"))


def parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
