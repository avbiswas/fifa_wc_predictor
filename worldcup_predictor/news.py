from __future__ import annotations

import json
import os

import requests


def search_news(team1: str, team2: str, max_results: int) -> list[dict]:
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        return [{"warning": "EXA_API_KEY not set; news search skipped."}]

    query = f"FIFA World Cup 2026 {team1} vs {team2} injuries lineup suspension team news"
    try:
        response = requests.post(
            "https://api.exa.ai/search",
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={
                "query": query,
                "type": "auto",
                "category": "news",
                "numResults": max_results,
                "contents": {"text": {"maxCharacters": 1200}, "highlights": {"numSentences": 3}},
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return [{"warning": f"Exa news search failed: {exc}"}]
    return response.json().get("results", [])


def format_news_items(items: list[dict]) -> str:
    rows = []
    for item in items:
        if "warning" in item:
            rows.append(item["warning"])
            continue
        text = item.get("text") or " ".join(item.get("highlights") or [])
        rows.append(
            json.dumps(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "publishedDate": item.get("publishedDate"),
                    "author": item.get("author"),
                    "text": text[:1200],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(rows) if rows else "No news results found."
