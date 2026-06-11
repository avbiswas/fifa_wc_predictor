from __future__ import annotations

import json
from pathlib import Path

from .cache import get_cached_or_fetch, load_retrieval_cache
from .data import get_match, normalize_match_key, squad_summary
from .env import load_env
from .news import format_news_items, search_news
from .paths import CACHE_PATH, DATA_DIR, ROOT
from .polymarket import polymarket_odds


PREPARED_DIR = ROOT / "data" / "prepared"


def prepare_match_data(
    match_id: int,
    news_results: int = 5,
    team1_record: str = "Unavailable in local dataset for this prototype.",
    team2_record: str = "Unavailable in local dataset for this prototype.",
    refresh_cache: bool = False,
    skip_news: bool = False,
    skip_polymarket: bool = False,
) -> dict:
    load_env()

    match_row = get_match(match_id)
    team1 = match_row["team1"]
    team2 = match_row["team2"]
    match_name = f"{team1} vs {team2}"
    cache = load_retrieval_cache()

    if skip_news:
        news_items = [{"warning": "News search skipped by CLI flag."}]
        news_from_cache = False
    else:
        news_items, news_from_cache = get_cached_or_fetch(
            cache,
            match_name,
            "news",
            refresh_cache,
            lambda: search_news(team1, team2, news_results),
        )

    if skip_polymarket:
        odds = [{"warning": "Polymarket lookup skipped by CLI flag."}]
        polymarket_from_cache = False
    else:
        odds, polymarket_from_cache = get_cached_or_fetch(
            cache,
            match_name,
            "polymarket",
            refresh_cache,
            lambda: polymarket_odds(team1, team2),
        )

    team1_squad = squad_summary(team1)
    team2_squad = squad_summary(team2)
    recent_record = f"{team1}: {team1_record}\n{team2}: {team2_record}"
    news_text = format_news_items(news_items)
    polymarket_odds_text = json.dumps(
        odds or [{"warning": "No matching Polymarket market found."}],
        indent=2,
        ensure_ascii=False,
    )

    return {
        "match_id": match_id,
        "match": match_name,
        "choices": [team1, team2, "Draw"],
        "match_row": match_row,
        "artifacts": {
            "news_items": news_items,
            "news_text": news_text,
            "polymarket_odds": odds,
            "polymarket_odds_text": polymarket_odds_text,
            "team1_squad": team1_squad,
            "team2_squad": team2_squad,
            "recent_record": recent_record,
        },
        "model_inputs": {
            "match": match_name,
            "match_context": json.dumps(match_row, ensure_ascii=False),
            "news_items": news_text,
            "team1_squad": team1_squad,
            "team2_squad": team2_squad,
            "recent_record": recent_record,
            "polymarket_odds": polymarket_odds_text,
        },
        "cache": {
            "path": str(CACHE_PATH.relative_to(ROOT)),
            "key": normalize_match_key(match_name),
            "news_from_cache": news_from_cache,
            "polymarket_from_cache": polymarket_from_cache,
        },
        "sources": {
            "schedule": str((DATA_DIR / "schedule_2026.csv").relative_to(ROOT)),
            "players": str((DATA_DIR / "players_2026.csv").relative_to(ROOT)),
        },
    }


def write_prepared_artifact(artifact: dict, output_path: Path | None = None) -> Path:
    path = output_path or PREPARED_DIR / f"match_{artifact['match_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
