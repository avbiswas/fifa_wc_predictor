from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
import re
import time
from typing import Any

import requests

from worldcup_predictor.tip_optimizer import Odds, american_to_decimal

ESPN_SCOREBOARD_URL = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
ESPN_SUMMARY_URL = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
ELO_BASE = "https://www.eloratings.net"
FIXTUREDOWNLOAD_URL = "https://fixturedownload.com/feed/json/fifa-world-cup-2026"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class MarketOdds:
    odds: Odds
    over_under: float | None
    spread: float | None
    provider: str | None
    source: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class EloTeam:
    code: str
    name: str
    rank: int | None
    rating: int | None


@dataclass(frozen=True)
class EloFixture:
    home_code: str
    away_code: str
    home_name: str
    away_name: str
    home_rank: int | None
    away_rank: int | None
    home_rating: int | None
    away_rating: int | None
    win_expectancy_home: float | None


def get_json(url: str, params: dict[str, Any] | None = None, *, timeout: int = 30) -> dict[str, Any] | list[Any]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - this is a resilient network client
            last_error = exc
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
    assert last_error is not None
    raise last_error


def get_text(url: str, *, timeout: int = 30) -> str:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    response.raise_for_status()
    return response.text


def date_range(start: datetime, days: int) -> str:
    dates = [(start + timedelta(days=offset)).strftime("%Y%m%d") for offset in range(days)]
    return dates[0] if len(dates) == 1 else f"{dates[0]}-{dates[-1]}"


def fetch_espn_scoreboard(dates: str) -> dict[str, Any]:
    data = get_json(ESPN_SCOREBOARD_URL, {"dates": dates})
    assert isinstance(data, dict)
    return data


def fetch_espn_summary(event_id: str) -> dict[str, Any]:
    data = get_json(ESPN_SUMMARY_URL, {"event": event_id})
    assert isinstance(data, dict)
    return data


def competitor_map(event: dict[str, Any]) -> dict[str, dict[str, Any]]:
    competitions = event.get("competitions") or []
    if not competitions:
        return {}
    return {competitor.get("homeAway"): competitor for competitor in competitions[0].get("competitors", [])}


def team_name(competitor: dict[str, Any]) -> str:
    team = competitor.get("team", {})
    return team.get("displayName") or team.get("shortDisplayName") or team.get("name") or "unknown"


def parse_espn_odds(summary: dict[str, Any]) -> MarketOdds | None:
    odds_rows = summary.get("odds") or summary.get("pickcenter") or []
    if not odds_rows:
        return None
    row = odds_rows[0]
    try:
        odds = Odds(
            home=american_to_decimal(row["homeTeamOdds"]["moneyLine"]),
            draw=american_to_decimal(row["drawOdds"]["moneyLine"]),
            away=american_to_decimal(row["awayTeamOdds"]["moneyLine"]),
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None
    return MarketOdds(
        odds=odds,
        over_under=row.get("overUnder"),
        spread=row.get("spread"),
        provider=(row.get("provider") or {}).get("name"),
        source="espn_draftkings",
        raw=row,
    )


def normalize_team_name(name: str) -> str:
    text = name.lower()
    replacements = {
        "bosnia-herzegovina": "bosnia and herzegovina",
        "bosnia & herzegovina": "bosnia and herzegovina",
        "congo dr": "dr congo",
        "congo, dr": "dr congo",
        "czechia": "czech republic",
        "cape verde": "cape verde islands",
        "curaçao": "curacao",
        "côte d’ivoire": "ivory coast",
        "côte d'ivoire": "ivory coast",
        "usa": "united states",
        "u.s.": "united states",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_int(value: str | None) -> int | None:
    if not value or not re.match(r"^-?\d+$", value):
        return None
    return int(value)


def fetch_elo_ratings() -> dict[str, EloTeam]:
    names_text = get_text(f"{ELO_BASE}/en.teams.tsv")
    names_by_code: dict[str, list[str]] = {}
    for line in names_text.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and not fields[0].endswith("_loc"):
            names_by_code[fields[0]] = fields[1:]

    world_text = get_text(f"{ELO_BASE}/World.tsv")
    ratings: dict[str, EloTeam] = {}
    for line in world_text.splitlines():
        fields = line.split("\t")
        if len(fields) < 4:
            continue
        code = fields[2]
        name = names_by_code.get(code, [code])[0]
        ratings[normalize_team_name(name)] = EloTeam(
            code=code,
            name=name,
            rank=parse_int(fields[0]),
            rating=parse_int(fields[3]),
        )
        for alias in names_by_code.get(code, [])[1:]:
            ratings[normalize_team_name(alias)] = ratings[normalize_team_name(name)]
    return ratings


def fetch_elo_fixtures() -> dict[tuple[str, str], EloFixture]:
    names_text = get_text(f"{ELO_BASE}/en.teams.tsv")
    names_by_code = {}
    for line in names_text.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and not fields[0].endswith("_loc"):
            names_by_code[fields[0]] = fields[1]
    fixtures_text = get_text(f"{ELO_BASE}/fixtures.tsv")
    fixtures: dict[tuple[str, str], EloFixture] = {}
    for line in fixtures_text.splitlines():
        fields = line.split("\t")
        if len(fields) < 12:
            continue
        home_name = names_by_code.get(fields[3], fields[3])
        away_name = names_by_code.get(fields[4], fields[4])
        fixture = EloFixture(
            home_code=fields[3],
            away_code=fields[4],
            home_name=home_name,
            away_name=away_name,
            home_rank=parse_int(fields[7]),
            away_rank=parse_int(fields[8]),
            home_rating=parse_int(fields[9]),
            away_rating=parse_int(fields[10]),
            win_expectancy_home=float(fields[11]) / 100 if re.match(r"^-?\d+(?:\.\d+)?$", fields[11]) else None,
        )
        fixtures[(normalize_team_name(home_name), normalize_team_name(away_name))] = fixture
        fixtures[(normalize_team_name(away_name), normalize_team_name(home_name))] = fixture
    return fixtures


def find_elo_fixture(home: str, away: str, fixtures: dict[tuple[str, str], EloFixture]) -> EloFixture | None:
    return fixtures.get((normalize_team_name(home), normalize_team_name(away)))


def find_elo_team(name: str, ratings: dict[str, EloTeam]) -> EloTeam | None:
    return ratings.get(normalize_team_name(name))


def form_summary(summary: dict[str, Any]) -> dict[str, list[str]]:
    form: dict[str, list[str]] = {}
    for side in summary.get("boxscore", {}).get("form", [])[:2]:
        name = side.get("team", {}).get("displayName")
        if not name:
            continue
        form[name] = [
            f"{event.get('gameDate', '')[:10]} {event.get('opponent', {}).get('displayName', '')} {event.get('score')} {event.get('gameResult')}"
            for event in side.get("events", [])[:5]
        ]
    return form


def form_points(events: list[str]) -> int | None:
    if not events:
        return None
    points = 0
    seen = 0
    for event in events:
        result = event.rsplit(" ", 1)[-1]
        if result == "W":
            points += 3
            seen += 1
        elif result == "D":
            points += 1
            seen += 1
        elif result == "L":
            seen += 1
    return points if seen else None


def news_headlines(summary: dict[str, Any]) -> list[str]:
    return [article.get("headline", "") for article in summary.get("news", {}).get("articles", [])[:5] if article.get("headline")]


def roster_counts(summary: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for side in summary.get("rosters", []) or []:
        team = (side.get("team") or {}).get("displayName")
        if team:
            counts[team] = len(side.get("roster", []) or [])
    return counts


def venue(summary: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    info = summary.get("gameInfo", {}) or {}
    venue_info = info.get("venue") or (event.get("competitions") or [{}])[0].get("venue") or {}
    address = venue_info.get("address") or {}
    return {
        "name": venue_info.get("fullName") or venue_info.get("name"),
        "city": address.get("city"),
        "country": address.get("country"),
    }


def fetch_weather(city: str | None, country: str | None, kickoff: datetime) -> dict[str, Any] | None:
    if not city:
        return None
    try:
        geo = get_json(OPEN_METEO_GEOCODE_URL, {"name": city, "count": 1, "language": "en", "format": "json"}, timeout=15)
        if not isinstance(geo, dict) or not geo.get("results"):
            return None
        location = geo["results"][0]
        forecast = get_json(
            OPEN_METEO_FORECAST_URL,
            {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,weather_code",
                "forecast_days": 7,
                "timezone": "UTC",
            },
            timeout=15,
        )
        if not isinstance(forecast, dict):
            return None
        hourly = forecast.get("hourly", {})
        times = hourly.get("time") or []
        if not times:
            return None
        target = kickoff.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M")
        index = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc) - kickoff))
        return {
            "source": "open_meteo",
            "city": city,
            "country": country,
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "forecast_time_utc": times[index],
            "target_hour_utc": target,
            "temperature_c": (hourly.get("temperature_2m") or [None])[index],
            "precipitation_probability_pct": (hourly.get("precipitation_probability") or [None])[index],
            "wind_speed_kmh": (hourly.get("wind_speed_10m") or [None])[index],
            "weather_code": (hourly.get("weather_code") or [None])[index],
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "open_meteo", "error": str(exc), "city": city, "country": country}


def fetch_fixturedownload() -> list[dict[str, Any]]:
    data = get_json(FIXTUREDOWNLOAD_URL)
    return data if isinstance(data, list) else []


def optional_source_status() -> dict[str, Any]:
    return {
        "the_odds_api_key": bool(os.getenv("THE_ODDS_API_KEY")),
        "api_football_key": bool(os.getenv("API_FOOTBALL_KEY") or os.getenv("APISPORTS_KEY")),
        "football_data_key": bool(os.getenv("FOOTBALL_DATA_API_KEY")),
    }
