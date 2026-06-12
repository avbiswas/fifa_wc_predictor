from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

import requests

from .data import get_match


SPORTSDB_URL = "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php"
WORLD_CUP_FEED_URL = "https://worldcup26.ir/get/games"
FINISHED_STATUSES = {"FT", "AET", "PEN"}


def fetch_match_result(match_id: int, fixture_id: int | None = None) -> dict:
    match = get_match(match_id)
    events = _get_json(
        SPORTSDB_URL,
        params={"id": 4429, "s": 2026},
    ).get("events") or []
    event = _find_match(
        events,
        match,
        home_key="strHomeTeam",
        away_key="strAwayTeam",
        id_key="idEvent",
        fixture_id=fixture_id,
    )
    if event.get("strStatus") not in FINISHED_STATUSES:
        raise SystemExit(
            f"TheSportsDB event {event.get('idEvent')} is not finished "
            f"(status={event.get('strStatus') or 'unknown'})."
        )

    team1_score, team2_score = _ordered_scores(
        match,
        event["strHomeTeam"],
        int(event["intHomeScore"]),
        int(event["intAwayScore"]),
    )
    goals = _fetch_goal_scorers(match)
    winner = match["team1"] if team1_score > team2_score else match["team2"] if team2_score > team1_score else "Draw"
    return {
        "match_id": match_id,
        "match": f"{match['team1']} vs {match['team2']}",
        "fixture_id": int(event["idEvent"]),
        "provider": "TheSportsDB",
        "status": event["strStatus"],
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "team1": match["team1"],
        "team2": match["team2"],
        "team1_score": team1_score,
        "team2_score": team2_score,
        "winner": winner,
        "goals": goals,
    }


def _fetch_goal_scorers(match: dict) -> list[dict]:
    try:
        games = _get_json(WORLD_CUP_FEED_URL).get("games") or []
        game = _find_match(
            games,
            match,
            home_key="home_team_name_en",
            away_key="away_team_name_en",
            id_key="id",
        )
    except (requests.RequestException, SystemExit, ValueError):
        return []

    goals = []
    for team_key, scorer_key in (
        ("home_team_name_en", "home_scorers"),
        ("away_team_name_en", "away_scorers"),
    ):
        for scorer in _parse_scorers(game.get(scorer_key)):
            goals.append({"team": game[team_key], **scorer})
    return goals


def _parse_scorers(value: object) -> list[dict]:
    if not isinstance(value, str) or value.casefold() == "null":
        return []
    normalized = value.translate(str.maketrans({"“": '"', "”": '"', "’": "'"}))
    entries = re.findall(r'"([^"]+)"', normalized)
    goals = []
    for entry in entries:
        match = re.match(r"(.+?)\s+(\d+)'$", entry.strip())
        goals.append(
            {
                "scorer": match.group(1).strip() if match else entry.strip(),
                "minute": int(match.group(2)) if match else None,
            }
        )
    return goals


def _find_match(
    rows: list[dict],
    match: dict,
    home_key: str,
    away_key: str,
    id_key: str,
    fixture_id: int | None = None,
) -> dict:
    if fixture_id is not None:
        candidates = [row for row in rows if str(row.get(id_key)) == str(fixture_id)]
    else:
        wanted = {_team_key(match["team1"]), _team_key(match["team2"])}
        candidates = [
            row
            for row in rows
            if {_team_key(row.get(home_key, "")), _team_key(row.get(away_key, ""))} == wanted
        ]
    if len(candidates) != 1:
        raise SystemExit(
            f"Expected one free result for {match['team1']} vs {match['team2']}; found {len(candidates)}."
        )
    return candidates[0]


def _ordered_scores(match: dict, home_name: str, home_score: int, away_score: int) -> tuple[int, int]:
    if _team_key(home_name) == _team_key(match["team1"]):
        return home_score, away_score
    return away_score, home_score


def _get_json(url: str, params: dict | None = None) -> dict:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _team_key(value: str) -> str:
    aliases = {
        "korearepublic": "southkorea",
        "czechia": "czechrepublic",
        "usa": "unitedstates",
        "unitedstatesofamerica": "unitedstates",
        "bosniaandherzegovina": "bosniaherzegovina",
        "cotedivoire": "ivorycoast",
        "congodr": "drcongo",
        "democraticrepublicofcongo": "drcongo",
        "capeverdeislands": "capeverde",
        "turkiye": "turkey",
    }
    normalized = unicodedata.normalize("NFKD", value)
    key = "".join(character for character in normalized if character.isascii() and character.isalnum()).casefold()
    return aliases.get(key, key)
