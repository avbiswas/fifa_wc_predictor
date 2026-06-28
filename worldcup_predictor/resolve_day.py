from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import datetime, timedelta, timezone

from .data import read_csv
from .env import load_env
from .models import competition_aliases, load_model_registry
from .paths import DATA_DIR, ROOT
from .predict_async import run_predictions_async
from .predictions import load_prediction_store, write_prediction_store
from .results import fetch_match_result
from .scoring import score_store, update_leaderboard


RESULT_RETRY_DELAY = timedelta(hours=1)
STATIC_SCHEDULE_PATH = ROOT / "cloudflare_app" / "public" / "data" / "schedule_2026.json"
SCHEDULE_CSV_PATH = DATA_DIR / "schedule_2026.csv"
SCHEDULE_JSON_PATH = DATA_DIR / "schedule_2026.json"
THIRD_PLACE_ANNEX_C = {
    "BDEFIJKL": {
        "3A/B/C/D/F": "D",
        "3C/D/F/G/H": "F",
        "3C/E/F/H/I": "E",
        "3E/H/I/J/K": "K",
        "3B/E/F/I/J": "B",
        "3A/E/H/I/J": "I",
        "3E/F/G/I/J": "J",
        "3D/E/I/J/L": "L",
    },
}


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
    schedule = read_csv(SCHEDULE_CSV_PATH)
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
    schedule, schedule_updates = resolve_knockout_fixtures(store, schedule, persist=not dry_run)
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
        "schedule_updates": schedule_updates,
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
        results = asyncio.run(run_predictions_async(
            match_id=match_id,
            aliases=missing,
            news_results=news_results,
        ))
        if results["predictions_run"]:
            predictions_changed = True
        summary["predictions_run"].extend(results["predictions_run"])
        summary["prediction_failures"].extend(results["prediction_failures"])

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
        "schedule_updates": summary.get("schedule_updates", []),
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


def resolve_knockout_fixtures(store: dict, schedule: list[dict], persist: bool = False) -> tuple[list[dict], list[dict]]:
    teams = knockout_teams(store, schedule)
    updated_schedule = [dict(match) for match in schedule]
    updates = []
    changed = False
    for match in updated_schedule:
        team1 = teams.get(match.get("team1", ""), match.get("team1", ""))
        team2 = teams.get(match.get("team2", ""), match.get("team2", ""))
        if team1 == match.get("team1") and team2 == match.get("team2"):
            continue
        old_match = f"{match.get('team1')} vs {match.get('team2')}"
        match["team1"] = team1
        match["team2"] = team2
        match["team1_code"] = team_code(schedule, team1)
        match["team2_code"] = team_code(schedule, team2)
        updates.append(
            {
                "match_id": int(match["match_id"]),
                "match_number": chronological_match_numbers(updated_schedule)[int(match["match_id"])],
                "from": old_match,
                "to": f"{team1} vs {team2}",
            }
        )
        changed = True
    if persist and changed:
        write_schedule(updated_schedule)
    return updated_schedule, updates


def knockout_teams(store: dict, schedule: list[dict]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    groups = group_standings(store, schedule)
    for group, table in groups.items():
        for index, row in enumerate(table[:3], start=1):
            resolved[f"{index}{group}"] = row["team"]

    third_groups = [group for group, table in best_third_place_groups(groups) if len(table) >= 3]
    if len(third_groups) == 8:
        third_slots = sorted(third_place_slots(schedule), key=lambda item: int(item["match_id"]))
        assignments = assign_third_place_groups(third_groups, third_slots)
        for slot, group in assignments.items():
            resolved[slot] = groups[group][2]["team"]

    for match_id, result in store.get("results", {}).items():
        winner = result.get("winner")
        if winner and winner != "Draw":
            resolved[f"W{match_id}"] = winner
        team1 = result.get("team1")
        team2 = result.get("team2")
        if winner and team1 and team2 and winner in {team1, team2}:
            resolved[f"L{match_id}"] = team2 if winner == team1 else team1
    return resolved


def group_standings(store: dict, schedule: list[dict]) -> dict[str, list[dict]]:
    teams_by_group: dict[str, list[str]] = {}
    match_ids_by_group: dict[str, set[str]] = {}
    for match in schedule:
        group = group_key(match)
        if not group:
            continue
        teams_by_group.setdefault(group, [])
        match_ids_by_group.setdefault(group, set()).add(str(match["match_id"]))
        for team in (match["team1"], match["team2"]):
            if team not in teams_by_group[group]:
                teams_by_group[group].append(team)

    rows = {
        team: {"team": team, "points": 0, "goal_difference": 0, "goals_for": 0}
        for teams in teams_by_group.values()
        for team in teams
    }
    schedule_by_id = {str(match["match_id"]): match for match in schedule}
    for match_id, result in store.get("results", {}).items():
        match = schedule_by_id.get(str(match_id))
        if not match or not group_key(match):
            continue
        team1 = result.get("team1") or match["team1"]
        team2 = result.get("team2") or match["team2"]
        if team1 not in rows or team2 not in rows:
            continue
        team1_score = int(result["team1_score"])
        team2_score = int(result["team2_score"])
        rows[team1]["goals_for"] += team1_score
        rows[team2]["goals_for"] += team2_score
        rows[team1]["goal_difference"] += team1_score - team2_score
        rows[team2]["goal_difference"] += team2_score - team1_score
        if team1_score > team2_score:
            rows[team1]["points"] += 3
        elif team2_score > team1_score:
            rows[team2]["points"] += 3
        else:
            rows[team1]["points"] += 1
            rows[team2]["points"] += 1

    standings = {}
    for group, teams in teams_by_group.items():
        if not match_ids_by_group[group].issubset(set(store.get("results", {}))):
            continue
        table = [rows[team] for team in teams]
        standings[group] = sorted(
            table,
            key=lambda row: (-row["points"], -row["goal_difference"], -row["goals_for"], row["team"]),
        )
    return standings


def best_third_place_groups(groups: dict[str, list[dict]]) -> list[tuple[str, list[dict]]]:
    thirds = [(group, table) for group, table in groups.items() if len(table) >= 3]
    return sorted(
        thirds,
        key=lambda item: (
            -item[1][2]["points"],
            -item[1][2]["goal_difference"],
            -item[1][2]["goals_for"],
            item[0],
        ),
    )[:8]


def third_place_slots(schedule: list[dict]) -> list[dict]:
    return [
        match
        for match in schedule
        if "/" in match.get("team1", "") or "/" in match.get("team2", "")
    ]


def assign_third_place_groups(third_groups: list[str], slots: list[dict]) -> dict[str, str]:
    annex_key = "".join(sorted(third_groups))
    if annex_key in THIRD_PLACE_ANNEX_C:
        return dict(THIRD_PLACE_ANNEX_C[annex_key])

    available = set(third_groups)
    slot_options = []
    for match in slots:
        for team_key in ("team1", "team2"):
            placeholder = match.get(team_key, "")
            if placeholder.startswith("3") and "/" in placeholder:
                options = placeholder[1:].split("/")
                slot_options.append((placeholder, [group for group in options if group in available]))

    assignments: dict[str, str] = {}

    def search(index: int, used: set[str]) -> bool:
        if index == len(slot_options):
            return True
        placeholder, options = slot_options[index]
        for group in options:
            if group in used:
                continue
            assignments[placeholder] = group
            if search(index + 1, used | {group}):
                return True
            assignments.pop(placeholder, None)
        return False

    search(0, set())
    return assignments


def team_code(schedule: list[dict], team: str) -> str:
    for match in schedule:
        if match.get("team1") == team and match.get("team1_code"):
            return match["team1_code"]
        if match.get("team2") == team and match.get("team2_code"):
            return match["team2_code"]
    return ""


def group_key(match: dict) -> str:
    group = (match.get("group") or "").strip()
    return group.removeprefix("Group ").strip()


def write_schedule(schedule: list[dict]) -> None:
    fieldnames = list(schedule[0].keys())
    with SCHEDULE_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(schedule)
    text = json.dumps(schedule, indent=2, ensure_ascii=False) + "\n"
    SCHEDULE_JSON_PATH.write_text(text, encoding="utf-8")
    STATIC_SCHEDULE_PATH.write_text(text, encoding="utf-8")


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
