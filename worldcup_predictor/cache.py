from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable

from .data import normalize_match_key
from .paths import CACHE_PATH


def load_retrieval_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"matches": {}}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def save_retrieval_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cached_match_entry(cache: dict, match_name: str) -> dict:
    return cache.setdefault("matches", {}).setdefault(normalize_match_key(match_name), {"match": match_name})


def get_cached_or_fetch(
    cache: dict,
    match_name: str,
    cache_field: str,
    refresh: bool,
    fetch: Callable[[], list[dict]],
) -> tuple[list[dict], bool]:
    entry = cached_match_entry(cache, match_name)
    if not refresh and cache_field in entry:
        return entry[cache_field]["data"], True

    data = fetch()
    entry[cache_field] = {
        "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }
    save_retrieval_cache(cache)
    return data, False
