from __future__ import annotations

import csv
import re
from pathlib import Path

from .paths import DATA_DIR


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def get_match(match_id: int) -> dict[str, str]:
    for row in read_csv(DATA_DIR / "schedule_2026.csv"):
        if int(row["match_id"]) == match_id:
            return row
    raise SystemExit(f"No match found for match_id={match_id}")


def normalize_match_key(match: str) -> str:
    return re.sub(r"\s+", " ", match.strip()).lower()


def split_match_string(match: str) -> tuple[str, str]:
    parts = re.split(r"\s+vs\.?\s+", match.strip(), flags=re.IGNORECASE)
    if len(parts) != 2 or not all(parts):
        raise SystemExit('Match must look like "Mexico vs South Africa".')
    return parts[0].strip(), parts[1].strip()


def get_match_by_string(match: str) -> dict[str, str]:
    team1, team2 = split_match_string(match)
    wanted = {team1.lower(), team2.lower()}
    for row in read_csv(DATA_DIR / "schedule_2026.csv"):
        teams = {row["team1"].lower(), row["team2"].lower()}
        if teams == wanted:
            return row
    raise SystemExit(f"No schedule row found for match={match!r}")


def squad_summary(team: str, limit_per_position: int = 8) -> str:
    players = [row for row in read_csv(DATA_DIR / "players_2026.csv") if row["team"] == team]
    by_position: dict[str, list[str]] = {"GK": [], "DF": [], "MF": [], "FW": []}
    for player in players:
        item = (
            f"{player['name_block']} | club={player['club']} | "
            f"caps={player['caps']} | goals={player['goals']} | height_cm={player['height_cm']}"
        )
        by_position.setdefault(player["position"], []).append(item)
    lines = []
    for position, items in by_position.items():
        visible = items[:limit_per_position]
        suffix = f" (+{len(items) - len(visible)} more)" if len(items) > len(visible) else ""
        lines.append(f"{position}: " + "; ".join(visible) + suffix)
    return "\n".join(lines)
