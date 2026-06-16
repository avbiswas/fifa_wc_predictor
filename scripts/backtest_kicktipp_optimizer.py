#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.tip_optimizer import exploit_engine_tip, ranked_market_tips, score_tip  # noqa: E402
from worldcup_predictor.kicktipp_archive import latest_archived_picks, record_event_key, scoreline_from_archived_record  # noqa: E402
from worldcup_predictor.tip_sources import (  # noqa: E402
    competitor_map,
    date_range,
    fetch_espn_scoreboard,
    fetch_espn_summary,
    parse_espn_odds,
    team_name,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backtest archived KickTipp exploit-engine picks against completed ESPN World Cup matches.")
    parser.add_argument("--days-back", type=int, default=14)
    parser.add_argument("--archive-dir", default="data/kicktipp/archive", help="Append-only pre-kickoff pick archive.")
    parser.add_argument(
        "--fallback-live-recompute",
        action="store_true",
        help="If no archived pick exists, recompute from current ESPN odds. Debug only; not a clean pre-kickoff backtest.",
    )
    parser.add_argument("--json-out", default="reports/kicktipp_optimizer_backtest.json")
    parser.add_argument("--markdown-out", default="reports/kicktipp_optimizer_backtest.md")
    return parser


def actual_score(event: dict[str, Any]) -> tuple[int, int] | None:
    competitors = competitor_map(event)
    if "home" not in competitors or "away" not in competitors:
        return None
    try:
        return int(competitors["home"].get("score", 0)), int(competitors["away"].get("score", 0))
    except (TypeError, ValueError):
        return None


def completed(event: dict[str, Any]) -> bool:
    competitions = event.get("competitions") or []
    if not competitions:
        return False
    return bool(((competitions[0].get("status") or {}).get("type") or {}).get("completed"))


def build_backtest(days_back: int, *, archive_dir: str | Path, fallback_live_recompute: bool = False) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days_back)
    archived_picks = latest_archived_picks(ROOT / archive_dir if not Path(archive_dir).is_absolute() else archive_dir)
    scoreboard = fetch_espn_scoreboard(date_range(start, days_back + 1))
    rows = []
    for event in scoreboard.get("events", []):
        if not completed(event):
            continue
        competitors = competitor_map(event)
        home = team_name(competitors["home"])
        away = team_name(competitors["away"])
        score = actual_score(event)
        if score is None:
            continue
        event_key = record_event_key({"event_id": event.get("id"), "match": f"{home} vs {away}", "kickoff_utc": event.get("date")})
        archived = archived_picks.get(event_key)
        if archived:
            predicted = scoreline_from_archived_record(archived)
            points = score_tip(predicted, score)
            row_data = archived.get("row") or {}
            rows.append(
                {
                    "event_id": event.get("id"),
                    "match": f"{home} vs {away}",
                    "kickoff_utc": event.get("date"),
                    "actual": f"{score[0]}:{score[1]}",
                    "tip": archived.get("final_tip"),
                    "selection_reason": (row_data.get("selection_reason") or "archived pre-kickoff leverage pick"),
                    "market_ev_tip": (row_data.get("ev_pick") or {}).get("scoreline"),
                    "market_ev_points": (row_data.get("ev_pick") or {}).get("expected_points"),
                    "actual_points": points,
                    "predicted_at": archived.get("generated_at"),
                    "archive_snapshot_id": archived.get("snapshot_id"),
                    "pick_source": "archive",
                    "status": "ok",
                }
            )
            continue

        if not fallback_live_recompute:
            rows.append(
                {
                    "event_id": event.get("id"),
                    "match": f"{home} vs {away}",
                    "kickoff_utc": event.get("date"),
                    "actual": f"{score[0]}:{score[1]}",
                    "status": "missing_archived_pick",
                    "pick_source": "missing_archive",
                }
            )
            continue

        summary = fetch_espn_summary(str(event["id"]))
        market = parse_espn_odds(summary)
        if not market:
            rows.append({"match": f"{home} vs {away}", "status": "missing_odds", "actual": f"{score[0]}:{score[1]}"})
            continue
        tip = exploit_engine_tip(market.odds, over_under=market.over_under)
        predicted = (tip.home_goals, tip.away_goals)
        market_top = ranked_market_tips(market.odds, over_under=market.over_under, limit=1)[0]
        points = score_tip(predicted, score)
        rows.append(
            {
                "match": f"{home} vs {away}",
                "kickoff_utc": event.get("date"),
                "actual": f"{score[0]}:{score[1]}",
                "tip": tip.scoreline,
                "selection_reason": tip.reason,
                "market_ev_tip": market_top.scoreline,
                "market_ev_points": round(market_top.expected_points, 3),
                "actual_points": points,
                "pick_source": "live_recompute",
                "status": "ok",
            }
        )
    scored = [row for row in rows if row.get("status") == "ok"]
    return {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "days_back": days_back,
        "archive_dir": str(archive_dir),
        "summary": {
            "matches": len(scored),
            "points": sum(row["actual_points"] for row in scored),
            "average_points": round(sum(row["actual_points"] for row in scored) / len(scored), 3) if scored else 0,
            "exact": sum(1 for row in scored if row["actual_points"] == 4),
            "nonzero": sum(1 for row in scored if row["actual_points"] > 0),
            "archived_matches": sum(1 for row in scored if row.get("pick_source") == "archive"),
            "live_recomputed_matches": sum(1 for row in scored if row.get("pick_source") == "live_recompute"),
            "missing_archived_picks": sum(1 for row in rows if row.get("status") == "missing_archived_pick"),
        },
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KickTipp optimizer backtest",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"Matches: **{summary['matches']}**, points: **{summary['points']}**, avg: **{summary['average_points']}**, exact: **{summary['exact']}**, nonzero: **{summary['nonzero']}**.",
        f"Archived picks: **{summary.get('archived_matches', 0)}**. Live recomputed fallback: **{summary.get('live_recomputed_matches', 0)}**. Missing archive: **{summary.get('missing_archived_picks', 0)}**.",
        "",
        "| Match | Actual | Tip | Points | Source | Predicted at | Market EV |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for row in report["rows"]:
        lines.append(f"| {row['match']} | {row.get('actual', '—')} | {row.get('tip', '—')} | {row.get('actual_points', '—')} | {row.get('pick_source', row.get('status', '—'))} | {row.get('predicted_at', '—')} | {row.get('market_ev_points', '—')} |")
    return "\n".join(lines) + "\n"


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
    report = build_backtest(args.days_back, archive_dir=args.archive_dir, fallback_live_recompute=args.fallback_live_recompute)
    json_path = resolve_output_path(args.json_out)
    md_path = resolve_output_path(args.markdown_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "json_out": display_path(json_path), "markdown_out": display_path(md_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
