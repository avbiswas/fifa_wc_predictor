#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.tip_optimizer import fair_probabilities, market_optimal_tip, score_tip  # noqa: E402
from worldcup_predictor.tip_sources import competitor_map, date_range, fetch_espn_scoreboard, fetch_espn_summary, parse_espn_odds  # noqa: E402

CONFIG_PATH = ROOT / "config" / "kicktipp_optimizer.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tune KickTipp exploit-engine draw-trap thresholds on completed World Cup matches.")
    parser.add_argument("--days-back", type=int, default=14)
    parser.add_argument("--config-out", default=str(CONFIG_PATH.relative_to(ROOT)))
    return parser


def collect_rows(days_back: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    scoreboard = fetch_espn_scoreboard(date_range(now - timedelta(days=days_back), days_back + 1))
    rows = []
    for event in scoreboard.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        if not (((comp.get("status") or {}).get("type") or {}).get("completed")):
            continue
        competitors = competitor_map(event)
        if "home" not in competitors or "away" not in competitors:
            continue
        try:
            actual = (int(competitors["home"].get("score", 0)), int(competitors["away"].get("score", 0)))
        except (TypeError, ValueError):
            continue
        market = parse_espn_odds(fetch_espn_summary(str(event["id"])))
        if not market:
            continue
        market_tip = market_optimal_tip(market.odds, over_under=market.over_under)
        rows.append({"event_id": event["id"], "actual": actual, "market": market, "market_tip": (market_tip.home_goals, market_tip.away_goals)})
    return rows


def score_thresholds(rows: list[dict], draw_floor: float, favorite_ceiling: float) -> int:
    points = 0
    for row in rows:
        fair = fair_probabilities(row["market"].odds)
        favorite_prob = max(fair["home"], fair["away"])
        predicted = (1, 1) if fair["draw"] >= draw_floor and favorite_prob < favorite_ceiling else row["market_tip"]
        points += score_tip(predicted, row["actual"])
    return points


def tune(rows: list[dict]) -> dict:
    best = []
    for floor_int in range(15, 31):
        for ceiling_int in range(55, 81):
            draw_floor = floor_int / 100
            favorite_ceiling = ceiling_int / 100
            points = score_thresholds(rows, draw_floor, favorite_ceiling)
            best.append((points, draw_floor, favorite_ceiling))
    best.sort(key=lambda item: (item[0], -abs(item[1] - 0.22), -abs(item[2] - 0.65)), reverse=True)
    top_points, top_floor, top_ceiling = best[0] if best else (0, 0.22, 0.65)
    return {
        "strategy": "kicktipp_exploit_engine",
        "draw_floor": top_floor,
        "draw_favorite_ceiling": top_ceiling,
        "tuned_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "training_matches": len(rows),
        "training_points": top_points,
        "training_average_points": round(top_points / len(rows), 3) if rows else 0,
        "top_grid": [
            {"points": points, "draw_floor": floor, "draw_favorite_ceiling": ceiling}
            for points, floor, ceiling in best[:10]
        ],
        "guardrails": {
            "note": "Thresholds are backtest-tuned on current tournament results. This is for KickTipp scoring, not betting.",
            "min_training_matches_for_trust": 12,
        },
    }


def resolve_output_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    args = build_parser().parse_args()
    rows = collect_rows(args.days_back)
    config = tune(rows)
    out = resolve_output_path(args.config_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"config_out": display_path(out), "training_matches": config["training_matches"], "training_points": config["training_points"], "draw_floor": config["draw_floor"], "draw_favorite_ceiling": config["draw_favorite_ceiling"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
