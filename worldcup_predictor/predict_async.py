from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import dspy

from .data import normalize_match_key
from .dspy_program import MatchPredictor, make_lm, summarize_news
from .env import load_env
from .goal_scorers import normalize_goal_scorers
from .models import default_model_alias, resolve_model
from .paths import PREDICTIONS_PATH, ROOT
from .predictions import load_prediction_store, write_prediction_store
from .prepare import prepare_match_data
from .usage import extract_lm_usage

_save_lock = asyncio.Lock()


async def _save_async(output: dict) -> None:
    async with _save_lock:
        store = load_prediction_store()
        stored = {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "key": f"{normalize_match_key(output['match'])}::{output['model']}",
            **output,
        }
        store.setdefault("predictions", []).append(stored)
        write_prediction_store(store)


async def _predict_one(
    alias: str,
    match_id: int,
    prepared: dict,
    news_summary: str,
    semaphore: asyncio.Semaphore,
) -> dict:
    async with semaphore:
        t0 = time.monotonic()
        model_alias, resolved_model = resolve_model(alias)
        lm = make_lm(resolved_model)
        team1, team2, _ = prepared["choices"]
        model_inputs = prepared["model_inputs"]

        predictor = MatchPredictor(team1, team2)
        print(f"  [{alias}] started", flush=True)
        with dspy.settings.context(lm=lm):
            result = await predictor.acall(
                match=model_inputs["match"],
                match_context=model_inputs["match_context"],
                news_summary=news_summary,
                team1_squad=model_inputs["team1_squad"],
                team2_squad=model_inputs["team2_squad"],
                recent_record=model_inputs["recent_record"],
                polymarket_odds=model_inputs["polymarket_odds"],
            )

        elapsed = time.monotonic() - t0
        output = {
            "match_id": match_id,
            "match": prepared["match"],
            "choices": [team1, team2, "Draw"],
            "model_alias": model_alias,
            "model": resolved_model,
            "prediction": result.prediction,
            "scoreline": result.scoreline,
            "goal_scorers": normalize_goal_scorers(result.goal_scorers),
            "confidence": result.confidence,
            "rationale": result.rationale,
            "usage": extract_lm_usage(lm),
            "news_summary": news_summary,
            "polymarket_odds": prepared["artifacts"]["polymarket_odds"],
        }
        print(f"  [{alias}] done in {elapsed:.1f}s — {result.prediction} ({result.scoreline})", flush=True)
        return output


async def run_predictions_async(
    match_id: int,
    aliases: list[str],
    news_results: int = 5,
    max_concurrent: int = 5,
) -> dict:
    load_env()
    prepared = prepare_match_data(match_id=match_id, news_results=news_results)
    match_name = prepared["match"]

    _, default_resolved = resolve_model(default_model_alias())
    default_lm = make_lm(default_resolved)
    print(f"[{match_name}] summarizing news...", flush=True)
    with dspy.settings.context(lm=default_lm):
        news_summary = summarize_news(match_name, prepared["model_inputs"]["news_items"])
    print(f"[{match_name}] running {len(aliases)} prediction(s) in parallel (max {max_concurrent} concurrent)...", flush=True)

    semaphore = asyncio.Semaphore(max_concurrent)
    successes: list[dict] = []
    failures: list[dict] = []

    async def run_one(alias: str) -> None:
        try:
            output = await _predict_one(alias, match_id, prepared, news_summary, semaphore)
            if not output["prediction"] or not output["scoreline"] or not output["rationale"]:
                raise ValueError("incomplete structured output from model")
            await _save_async(output)
            successes.append({"match_id": match_id, "model": alias})
        except Exception as exc:
            print(f"  [{alias}] failed: {exc}", flush=True)
            failures.append({"match_id": match_id, "model": alias, "error": str(exc)})

    await asyncio.gather(*[run_one(alias) for alias in aliases])
    print(f"[{match_name}] {len(successes)} succeeded, {len(failures)} failed", flush=True)
    return {"predictions_run": successes, "prediction_failures": failures}
