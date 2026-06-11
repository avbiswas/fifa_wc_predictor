from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .paths import CACHE_PATH, DATA_DIR, PREDICTIONS_PATH, ROOT


console = Console()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def add_rows(table: Table, rows: list[dict[str, str]], fields: list[str]) -> None:
    for row in rows:
        table.add_row(*(str(row.get(field, "")) for field in fields))


def show_counts() -> None:
    table = Table(title="Processed Data")
    table.add_column("File")
    table.add_column("Rows", justify="right")
    for name in [
        "schedule_2026.csv",
        "teams_2026.csv",
        "players_2026.csv",
        "coaches_2026.csv",
        "grounds_2026.csv",
        "sources.csv",
    ]:
        rows = read_csv(DATA_DIR / name)
        table.add_row(name, str(len(rows)))
    console.print(table)


def show_match(match_id: int, squad_limit: int | None) -> None:
    schedule = read_csv(DATA_DIR / "schedule_2026.csv")
    match = next((row for row in schedule if int(row["match_id"]) == match_id), None)
    if not match:
        raise SystemExit(f"No match found for match_id={match_id}")

    console.print(Panel.fit(f"{match['team1']} vs {match['team2']}", title=f"Match {match_id}"))
    table = Table(title="Schedule")
    for key in match:
        table.add_column(key)
    table.add_row(*(match[key] for key in match))
    console.print(table)

    teams = {match["team1"], match["team2"]}
    team_rows = [row for row in read_csv(DATA_DIR / "teams_2026.csv") if row["team"] in teams]
    team_table = Table(title="Teams")
    fields = ["team", "team_code", "group", "roster_size", "coach_block", "coach_nationality"]
    for field in fields:
        team_table.add_column(field)
    add_rows(team_table, team_rows, fields)
    console.print(team_table)

    players = read_csv(DATA_DIR / "players_2026.csv")
    for team in [match["team1"], match["team2"]]:
        player_table = Table(title=f"{team} Squad")
        fields = ["roster_index", "position", "name_block", "club", "caps", "goals", "height_cm"]
        for field in fields:
            player_table.add_column(field)
        team_players = [row for row in players if row["team"] == team]
        visible_players = team_players if squad_limit is None else team_players[:squad_limit]
        add_rows(player_table, visible_players, fields)
        if squad_limit is not None and len(team_players) > squad_limit:
            player_table.caption = f"Showing {squad_limit} of {len(team_players)} players. Use --all-players for full squads."
        console.print(player_table)


def show_prepared(match_id: int) -> None:
    path = ROOT / "data" / "prepared" / f"match_{match_id}.json"
    if not path.exists():
        console.print(f"[yellow]No prepared artifact found at {path.relative_to(ROOT)}. Run ./prepare_data {match_id} first.[/yellow]")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    console.print(Panel.fit(data["match"], title="Prepared Artifact"))
    console.print_json(json.dumps(data["cache"], ensure_ascii=False))
    console.print(Panel(data["artifacts"]["news_text"][:3000], title="News Text"))
    console.print(Panel(data["artifacts"]["polymarket_odds_text"][:3000], title="Polymarket Odds"))


def show_cache() -> None:
    if not CACHE_PATH.exists():
        console.print("[yellow]No cache file found.[/yellow]")
        return
    data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    table = Table(title="Retrieval Cache")
    table.add_column("Match Key")
    table.add_column("Has News")
    table.add_column("Has Polymarket")
    for key, entry in data.get("matches", {}).items():
        table.add_row(key, str("news" in entry), str("polymarket" in entry))
    console.print(table)


def show_predictions() -> None:
    if not PREDICTIONS_PATH.exists():
        console.print("[yellow]No prediction history file found.[/yellow]")
        return
    data = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    table = Table(title="Prediction History")
    for column in ["created_at", "model_alias", "model", "match", "prediction", "scoreline", "tokens", "cost", "confidence"]:
        table.add_column(column)
    for row in data.get("predictions", [])[-20:]:
        usage = row.get("usage", {}).get("totals", {})
        table.add_row(
            row.get("created_at", ""),
            row.get("model_alias", ""),
            row.get("model", ""),
            row.get("match", ""),
            row.get("prediction", ""),
            row.get("scoreline", ""),
            str(usage.get("total_tokens", "")),
            str(usage.get("cost", "")),
            str(row.get("confidence", "")),
        )
    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pretty-print downloaded World Cup data with Rich.")
    parser.add_argument("--match-id", type=int, default=1)
    parser.add_argument("--prepared", action="store_true")
    parser.add_argument("--cache", action="store_true")
    parser.add_argument("--predictions", action="store_true")
    parser.add_argument("--squad-limit", type=int, default=8)
    parser.add_argument("--all-players", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    show_counts()
    show_match(args.match_id, None if args.all_players else args.squad_limit)
    if args.prepared:
        show_prepared(args.match_id)
    if args.cache:
        show_cache()
    if args.predictions:
        show_predictions()
    return 0
