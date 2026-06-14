from __future__ import annotations

import argparse
import json

from .data import get_match_by_string, normalize_match_key
from .dspy_program import MatchPredictor, configure_dspy, summarize_news
from .env import load_env
from .models import default_model_alias, model_registry_rows, resolve_model, validate_openrouter_models
from .paths import CACHE_PATH, ROOT
from .goal_scorers import normalize_goal_scorers
from .predictions import load_prediction_store, model_performance_context, save_prediction_record
from .prepare import prepare_match_data
from .usage import extract_lm_usage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("match", nargs="?", help='Match string, e.g. "Mexico vs South Africa".')
    parser.add_argument("--match-id", type=int, default=1)
    parser.add_argument("--news-results", type=int, default=5)
    parser.add_argument("--team1-record", default="Unavailable in local dataset for this prototype.")
    parser.add_argument("--team2-record", default="Unavailable in local dataset for this prototype.")
    parser.add_argument("--skip-news", action="store_true")
    parser.add_argument("--skip-polymarket", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--model", default=default_model_alias(), help="Competition alias or full LiteLLM/OpenRouter model string.")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--validate-models", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list_models:
        print(json.dumps(model_registry_rows(), indent=2, ensure_ascii=False))
        return 0
    if args.validate_models:
        print(json.dumps(validate_openrouter_models(), indent=2, ensure_ascii=False))
        return 0

    load_env()
    model_alias, resolved_model = resolve_model(args.model)
    lm = configure_dspy(resolved_model)

    match_id = int(get_match_by_string(args.match)["match_id"]) if args.match else args.match_id
    prepared = prepare_match_data(
        match_id=match_id,
        news_results=args.news_results,
        team1_record=args.team1_record,
        team2_record=args.team2_record,
        refresh_cache=args.refresh_cache,
        skip_news=args.skip_news,
        skip_polymarket=args.skip_polymarket,
    )
    team1, team2, _ = prepared["choices"]
    match_name = prepared["match"]
    model_inputs = prepared["model_inputs"]
    artifacts = prepared["artifacts"]
    news_summary = summarize_news(match_name, model_inputs["news_items"])
    performance_history = model_performance_context(
        load_prediction_store(),
        model_alias=model_alias,
        model=resolved_model,
        current_match_id=match_id,
    )
    predictor = MatchPredictor(team1, team2)
    result = predictor(
        match=model_inputs["match"],
        match_context=model_inputs["match_context"],
        news_summary=news_summary,
        team1_squad=model_inputs["team1_squad"],
        team2_squad=model_inputs["team2_squad"],
        recent_record=model_inputs["recent_record"],
        performance_history=performance_history,
        polymarket_odds=model_inputs["polymarket_odds"],
    )

    output = {
        "match_id": match_id,
        "match": match_name,
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
        "performance_history": performance_history,
        "polymarket_odds": artifacts["polymarket_odds"],
        "cache": {
            "path": str(CACHE_PATH.relative_to(ROOT)),
            "key": normalize_match_key(match_name),
            "news_from_cache": prepared["cache"]["news_from_cache"],
            "polymarket_from_cache": prepared["cache"]["polymarket_from_cache"],
        },
    }
    if not args.no_save:
        if not output["prediction"] or not output["scoreline"] or not output["rationale"]:
            raise SystemExit("Model returned incomplete structured output; not saving prediction.")
        output["saved_to"] = save_prediction_record(output)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0
