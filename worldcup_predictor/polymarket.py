from __future__ import annotations

import json

import requests


POLYMARKET_SEARCH_ENDPOINTS = [
    {
        "name": "global_gamma",
        "url": "https://gamma-api.polymarket.com/public-search",
        "params": lambda query: {
            "q": query,
            "limit_per_type": 10,
            "search_tags": "false",
            "search_profiles": "false",
        },
    },
    {
        "name": "us_gateway",
        "url": "https://gateway.polymarket.us/v1/search",
        "params": lambda query: {
            "query": query,
            "limit": 10,
        },
    },
]


def polymarket_odds(team1: str, team2: str) -> list[dict]:
    query = f"{team1} {team2} World Cup"
    failures = []
    for endpoint in POLYMARKET_SEARCH_ENDPOINTS:
        try:
            response = requests.get(
                endpoint["url"],
                params=endpoint["params"](query),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            failures.append({"endpoint": endpoint["name"], "url": endpoint["url"], "error": str(exc)})
            continue

        matches = extract_relevant_markets(response.json(), team1, team2)
        if matches:
            return matches
        failures.append(
            {
                "endpoint": endpoint["name"],
                "url": endpoint["url"],
                "error": "Request succeeded but no matching market was found.",
            }
        )

    return [{"warning": "Polymarket lookup failed or found no market.", "failures": failures}]


def extract_relevant_markets(payload: object, team1: str, team2: str) -> list[dict]:
    records = normalize_search_records(payload)
    matches = []
    for record in records:
        blob = json.dumps(record, ensure_ascii=False).lower()
        if team1.lower() not in blob or team2.lower() not in blob:
            continue

        title = record.get("title") or record.get("question") or record.get("name") or ""
        markets = record.get("markets") or [record]
        extracted_markets = [extract_market(market, title, record) for market in markets[:5]]
        matches.append({"title": title, "slug": record.get("slug"), "markets": extracted_markets})
    return matches[:3]


def normalize_search_records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if not isinstance(payload, dict):
        return []
    records = []
    for key in ("events", "markets", "results"):
        value = payload.get(key) or []
        if isinstance(value, list):
            records.extend(record for record in value if isinstance(record, dict))
    return records


def extract_market(market: dict, title: str, record: dict) -> dict:
    return {
        "question": market.get("question") or market.get("title") or title,
        "outcomes": parse_jsonish_list(market.get("outcomes")),
        "outcome_prices": parse_jsonish_list(market.get("outcomePrices") or market.get("outcome_prices")),
        "volume": market.get("volume") or market.get("volumeNum"),
        "liquidity": market.get("liquidity") or market.get("liquidityNum"),
        "url": market.get("url") or record.get("url"),
        "source_slug": market.get("slug") or record.get("slug"),
    }


def parse_jsonish_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [value]
    return [value]
