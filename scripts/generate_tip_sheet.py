#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "kicktipp_optimizer.json"
sys.path.insert(0, str(ROOT))

from worldcup_predictor.tip_optimizer import (  # noqa: E402
    expected_tip_points,
    exploit_engine_tip,
    fair_probabilities,
    fit_market_lambdas,
    poisson_distribution,
    ranked_market_tips,
    risk_tier,
)
from worldcup_predictor.tip_sources import (  # noqa: E402
    date_range,
    fetch_elo_fixtures,
    fetch_elo_ratings,
    fetch_espn_scoreboard,
    fetch_espn_summary,
    fetch_weather,
    find_elo_fixture,
    find_elo_team,
    form_points,
    form_summary,
    news_headlines,
    optional_source_status,
    parse_espn_odds,
    roster_counts,
    team_name,
    competitor_map,
    venue,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a source-backed KickTipp exploit-engine baseline sheet: odds -> fair probabilities -> Poisson -> expected-points scorelines."
    )
    parser.add_argument("--days", type=int, default=3, help="Calendar days starting from --date/today UTC.")
    parser.add_argument("--date", help="Start date YYYYMMDD. Defaults to today UTC.")
    parser.add_argument("--hours", type=float, help="Only include matches within this many hours from now.")
    parser.add_argument("--include-started", action="store_true", help="Include matches whose kickoff already passed.")
    parser.add_argument("--no-weather", action="store_true", help="Skip Open-Meteo venue weather enrichment.")
    parser.add_argument("--json-out", default="reports/tip_sheet.json")
    parser.add_argument("--markdown-out", default="reports/tip_sheet.md")
    parser.add_argument("--compact", action="store_true", help="Print compact tips only.")
    return parser


def load_optimizer_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"draw_floor": 0.22, "draw_favorite_ceiling": 0.65, "source": "defaults"}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {
            "draw_floor": float(data.get("draw_floor", 0.22)),
            "draw_favorite_ceiling": float(data.get("draw_favorite_ceiling", 0.65)),
            "source": str(CONFIG_PATH.relative_to(ROOT)),
            "training_matches": data.get("training_matches"),
            "training_points": data.get("training_points"),
            "tuned_at": data.get("tuned_at"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"draw_floor": 0.22, "draw_favorite_ceiling": 0.65, "source": f"defaults_after_config_error: {exc}"}


def parse_kickoff(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def decimal_or_none(value: Any) -> float | None:
    try:
        return float(str(value).replace("+", ""))
    except (TypeError, ValueError):
        return None


def movement_summary(raw_odds: dict[str, Any]) -> dict[str, Any] | None:
    moneyline = raw_odds.get("moneyline") or {}
    out: dict[str, Any] = {}
    for side in ["home", "draw", "away"]:
        close = decimal_or_none(((moneyline.get(side) or {}).get("close") or {}).get("odds"))
        open_ = decimal_or_none(((moneyline.get(side) or {}).get("open") or {}).get("odds"))
        if close is None or open_ is None:
            continue
        out[side] = {"open_american": open_, "close_american": close, "delta_american": close - open_}
    if not out:
        return None
    big = [side for side, row in out.items() if abs(row["delta_american"]) >= 120]
    return {"sides": out, "flags": [f"big_{side}_move" for side in big]}


def risk_flags(row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    fair = row.get("fair_probabilities") or {}
    top = max(fair.get("home", 0), fair.get("away", 0))
    if fair.get("draw", 0) >= 0.24 and top < 0.62:
        flags.append("draw_trap")
    if row.get("risk_tier") in {"thin_edge", "chaos"}:
        flags.append("low_edge")
    weather = row.get("weather") or {}
    if weather.get("precipitation_probability_pct") is not None and weather["precipitation_probability_pct"] >= 55:
        flags.append("wet_weather")
    if weather.get("wind_speed_kmh") is not None and weather["wind_speed_kmh"] >= 28:
        flags.append("wind")
    movement = row.get("market_movement") or {}
    flags.extend(movement.get("flags") or [])
    return flags


def build_tip_sheet(days: int, start_date: str | None, include_started: bool, hours: float | None, weather: bool) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = datetime.strptime(start_date, "%Y%m%d").replace(tzinfo=timezone.utc) if start_date else now
    end = now + timedelta(hours=hours) if hours else None
    scoreboard = fetch_espn_scoreboard(date_range(start, days))
    try:
        elo_fixtures = fetch_elo_fixtures()
        elo_ratings = fetch_elo_ratings()
        elo_status = "ok"
    except Exception as exc:  # noqa: BLE001
        elo_fixtures = {}
        elo_ratings = {}
        elo_status = f"error: {exc}"

    optimizer_config = load_optimizer_config()
    rows: list[dict[str, Any]] = []
    for event in scoreboard.get("events", []):
        kickoff = parse_kickoff(event["date"])
        if not include_started and kickoff <= now:
            continue
        if end and kickoff > end:
            continue
        competitors = competitor_map(event)
        if "home" not in competitors or "away" not in competitors:
            continue
        home = team_name(competitors["home"])
        away = team_name(competitors["away"])
        summary = fetch_espn_summary(str(event["id"]))
        market = parse_espn_odds(summary)
        base: dict[str, Any] = {
            "event_id": event["id"],
            "kickoff_utc": event["date"],
            "match": f"{home} vs {away}",
            "home": home,
            "away": away,
            "status": "ok" if market else "missing_odds",
        }
        match_venue = venue(summary, event)
        base["venue"] = match_venue
        base["news"] = news_headlines(summary)
        base["form"] = form_summary(summary)
        base["form_points"] = {team: form_points(events) for team, events in base["form"].items()}
        base["roster_counts"] = roster_counts(summary)
        elo_fixture = find_elo_fixture(home, away, elo_fixtures)
        home_elo = find_elo_team(home, elo_ratings)
        away_elo = find_elo_team(away, elo_ratings)
        if elo_fixture:
            base["elo"] = {
                "source": "eloratings.net fixtures.tsv",
                "home_rating": elo_fixture.home_rating,
                "away_rating": elo_fixture.away_rating,
                "home_rank": elo_fixture.home_rank,
                "away_rank": elo_fixture.away_rank,
                "rating_diff_home": (elo_fixture.home_rating - elo_fixture.away_rating) if elo_fixture.home_rating and elo_fixture.away_rating else None,
                "win_expectancy_home": elo_fixture.win_expectancy_home,
            }
        elif home_elo or away_elo:
            base["elo"] = {
                "source": "eloratings.net World.tsv",
                "home_rating": home_elo.rating if home_elo else None,
                "away_rating": away_elo.rating if away_elo else None,
                "home_rank": home_elo.rank if home_elo else None,
                "away_rank": away_elo.rank if away_elo else None,
                "rating_diff_home": (home_elo.rating - away_elo.rating) if home_elo and away_elo and home_elo.rating and away_elo.rating else None,
            }
        else:
            base["elo"] = {"source": "eloratings.net", "status": "missing"}
        if weather:
            base["weather"] = fetch_weather(match_venue.get("city"), match_venue.get("country"), kickoff)
        if not market:
            rows.append(base)
            continue

        fair = fair_probabilities(market.odds)
        home_lambda, away_lambda, fitted_probs = fit_market_lambdas(market.odds, over_under=market.over_under)
        candidates = ranked_market_tips(market.odds, over_under=market.over_under, limit=8)
        chosen = exploit_engine_tip(
            market.odds,
            over_under=market.over_under,
            draw_floor=optimizer_config["draw_floor"],
            draw_favorite_ceiling=optimizer_config["draw_favorite_ceiling"],
        )
        chosen_score = (chosen.home_goals, chosen.away_goals)
        distribution = poisson_distribution(home_lambda, away_lambda)
        chosen_expected = expected_tip_points(chosen_score, distribution)
        top = candidates[0]
        base.update(
            {
                "tip": chosen.scoreline,
                "pick": chosen.pick,
                "selection_reason": chosen.reason,
                "expected_points": round(chosen_expected, 3),
                "market_ev_tip": top.scoreline,
                "market_ev_points": round(top.expected_points, 3),
                "exact_probability": round(distribution.get(chosen_score, 0.0), 4),
                "outcome_probability": round(fitted_probs[chosen.pick], 4),
                "risk_tier": risk_tier(candidates),
                "odds_decimal": {
                    "home": round(market.odds.home, 3),
                    "draw": round(market.odds.draw, 3),
                    "away": round(market.odds.away, 3),
                },
                "fair_probabilities": {key: round(value, 4) for key, value in fair.items()},
                "fitted_probabilities": {key: round(value, 4) for key, value in fitted_probs.items()},
                "fitted_lambdas": {"home": home_lambda, "away": away_lambda},
                "over_under": market.over_under,
                "spread": market.spread,
                "provider": market.provider,
                "source": market.source,
                "top_alternatives": [
                    {
                        "scoreline": candidate.scoreline,
                        "pick": candidate.pick,
                        "expected_points": round(candidate.expected_points, 3),
                        "exact_probability": round(candidate.exact_probability, 4),
                        "outcome_probability": round(candidate.outcome_probability, 4),
                    }
                    for candidate in candidates
                ],
                "market_movement": movement_summary(market.raw),
            }
        )
        base["risk_flags"] = risk_flags(base)
        rows.append(base)

    return {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "source_status": {"espn": "ok", "elo": elo_status, "weather": "enabled" if weather else "disabled", **optional_source_status()},
        "rules": {"exact": 4, "tendency": 2, "win_goal_difference": 3, "non_exact_draw": 2, "knockout_basis": "after penalties"},
        "optimizer_config": optimizer_config,
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# KickTipp exploit-engine baseline sheet",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "Rules optimized: exact=4, tendency=2, win goal-difference=3, non-exact draw=2, knockout result after penalties.",
        f"Optimizer config: `{report.get('optimizer_config', {}).get('source')}` draw_floor={report.get('optimizer_config', {}).get('draw_floor')} favorite_ceiling={report.get('optimizer_config', {}).get('draw_favorite_ceiling')}.",
        "",
        "## Put these in",
        "",
        "| Kickoff UTC | Match | Tip | Risk | EV | Fair 1/X/2 | Odds 1/X/2 | Flags |",
        "|---|---|---:|---|---:|---|---|---|",
    ]
    for row in report["rows"]:
        if row.get("status") != "ok":
            lines.append(f"| {row.get('kickoff_utc')} | {row.get('match')} | — | — | — | — | — | missing odds |")
            continue
        fair = row["fair_probabilities"]
        odds = row["odds_decimal"]
        flags = ", ".join(row.get("risk_flags") or []) or "—"
        lines.append(
            f"| {row['kickoff_utc']} | {row['match']} | **{row['tip']}** | {row['risk_tier']} | {row['expected_points']:.2f} | "
            f"{fair['home']:.1%}/{fair['draw']:.1%}/{fair['away']:.1%} | "
            f"{odds['home']}/{odds['draw']}/{odds['away']} | {flags} |"
        )
    lines += ["", "## Evidence / alternatives", ""]
    for row in report["rows"]:
        lines.append(f"### {row.get('match')}")
        if row.get("status") != "ok":
            lines.append("- No usable odds returned. Do not trust a blind LLM pick here.")
            lines.append("")
            continue
        lines.append(
            f"- Tip **{row['tip']}** ({row['risk_tier']}, EV {row['expected_points']:.2f}); market-EV baseline {row.get('market_ev_tip')} ({row.get('market_ev_points')}); model λ {row['fitted_lambdas']['home']:.2f}-{row['fitted_lambdas']['away']:.2f}; O/U {row.get('over_under')}."
        )
        if row.get("selection_reason"):
            lines.append(f"- Selection: {row['selection_reason']}.")
        elo = row.get("elo") or {}
        if elo.get("rating_diff_home") is not None:
            lines.append(
                f"- Elo: {row['home']} {elo.get('home_rating')} vs {row['away']} {elo.get('away_rating')} (home diff {elo.get('rating_diff_home')})."
            )
        weather = row.get("weather") or {}
        if weather and not weather.get("error"):
            lines.append(
                f"- Weather: {weather.get('temperature_c')}°C, rain {weather.get('precipitation_probability_pct')}%, wind {weather.get('wind_speed_kmh')} km/h at {weather.get('city')}."
            )
        alternatives = ", ".join(f"{a['scoreline']}({a['expected_points']:.2f})" for a in row.get("top_alternatives", [])[:5])
        lines.append(f"- Alternatives: {alternatives}.")
        movement = row.get("market_movement") or {}
        if movement.get("flags"):
            lines.append(f"- Market movement flags: {', '.join(movement['flags'])}.")
        headlines = row.get("news") or []
        if headlines:
            lines.append("- News: " + " | ".join(headlines[:2]))
        lines.append("")
    lines += ["## Source status", "", "```json", json.dumps(report.get("source_status", {}), indent=2, ensure_ascii=False), "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def compact_output(report: dict[str, Any]) -> str:
    rows = [row for row in report["rows"] if row.get("status") == "ok"]
    if not rows:
        return "No usable tips — odds missing."
    return "\n".join(f"{row['match']}: {row['tip']} ({row['risk_tier']}, EV {row['expected_points']:.2f})" for row in rows)


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
    report = build_tip_sheet(args.days, args.date, args.include_started, args.hours, not args.no_weather)
    json_path = resolve_output_path(args.json_out)
    md_path = resolve_output_path(args.markdown_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if args.compact:
        print(compact_output(report))
    else:
        print(json.dumps({
            "tips": [{"match": row.get("match"), "tip": row.get("tip"), "risk": row.get("risk_tier"), "status": row.get("status")} for row in report["rows"]],
            "json_out": display_path(json_path),
            "markdown_out": display_path(md_path),
        }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
