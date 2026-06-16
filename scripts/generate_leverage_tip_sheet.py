#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_tip_sheet import build_tip_sheet  # noqa: E402
from worldcup_predictor.leverage_optimizer import (  # noqa: E402
    MODE_WEIGHTS,
    Odds,
    apply_slate_draw_budget,
    choose_mode_from_state,
    known_predictions_for_match,
    load_kicktipp_context,
    optimize_match,
    slate_draw_target,
)

DEFAULT_CONTEXT = ROOT / "data" / "kicktipp" / "rounds.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate private-league KickTipp picks optimized for EV + leverage against friends.")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--date", help="Start date YYYYMMDD. Defaults to today UTC.")
    parser.add_argument("--hours", type=float, help="Only include matches within this many hours from now.")
    parser.add_argument("--include-started", action="store_true")
    parser.add_argument("--no-weather", action="store_true")
    parser.add_argument("--mode", choices=sorted(MODE_WEIGHTS), help="Override mode from KickTipp context.")
    parser.add_argument("--context", default=str(DEFAULT_CONTEXT), help="KickTipp friend/standings context JSON.")
    parser.add_argument("--target-draws", type=int, help="Override slate draw budget.")
    parser.add_argument("--json-out", default="reports/leverage_tip_sheet.json")
    parser.add_argument("--markdown-out", default="reports/leverage_tip_sheet.md")
    parser.add_argument("--compact", action="store_true")
    return parser


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


def rounded_nested(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: rounded_nested(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [rounded_nested(inner) for inner in value]
    return value


def build_leverage_sheet(
    *,
    days: int,
    date: str | None,
    include_started: bool,
    hours: float | None,
    weather: bool,
    context_path: str | Path | None,
    mode_override: str | None = None,
    target_draws: int | None = None,
) -> dict[str, Any]:
    context = load_kicktipp_context(context_path)
    state = context.get("current_state") or {}
    mode = mode_override or choose_mode_from_state(state)
    source = build_tip_sheet(days, date, include_started, hours, weather)
    rows: list[dict[str, Any]] = []
    for row in source.get("rows", []):
        if row.get("status") != "ok":
            rows.append({
                "event_id": row.get("event_id"),
                "kickoff_utc": row.get("kickoff_utc"),
                "match": row.get("match"),
                "status": row.get("status"),
                "reason": "missing odds; no leverage optimization possible",
            })
            continue
        odds_row = row["odds_decimal"]
        odds = Odds(home=float(odds_row["home"]), draw=float(odds_row["draw"]), away=float(odds_row["away"]))
        known_field, known_leaders = known_predictions_for_match(context, event_id=row.get("event_id"), match=row.get("match"))
        optimized = optimize_match(
            match=row["match"],
            odds=odds,
            over_under=row.get("over_under"),
            field_predictions=known_field or None,
            leader_predictions=known_leaders or None,
            mode=mode,
        )
        optimized.update(
            {
                "event_id": row.get("event_id"),
                "kickoff_utc": row.get("kickoff_utc"),
                "home": row.get("home"),
                "away": row.get("away"),
                "status": "ok",
                "baseline_tip": row.get("tip"),
                "baseline_reason": row.get("selection_reason"),
                "source_risk_tier": row.get("risk_tier"),
                "source_risk_flags": row.get("risk_flags") or [],
                "provider": row.get("provider"),
                "news": row.get("news") or [],
                "weather": row.get("weather"),
                "elo": row.get("elo"),
                "known_field_used": [f"{h}:{a}" for h, a in known_field],
                "known_leaders_used": [f"{h}:{a}" for h, a in known_leaders],
            }
        )
        rows.append(rounded_nested(optimized))

    ok_rows = [row for row in rows if row.get("status") == "ok"]
    auto_target = slate_draw_target([float(row.get("fair_probabilities", {}).get("draw", 0.0)) for row in ok_rows])
    adjusted_ok = apply_slate_draw_budget(ok_rows, target_draws=target_draws if target_draws is not None else auto_target)
    adjusted_by_id = {row.get("event_id"): row for row in adjusted_ok}
    final_rows = [adjusted_by_id.get(row.get("event_id"), row) if row.get("status") == "ok" else row for row in rows]
    final_draws = sum(1 for row in final_rows if (row.get("final_pick") or {}).get("pick") == "draw")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "context_path": str(context_path) if context_path else None,
        "current_state": state,
        "rules": source.get("rules"),
        "draw_budget": {
            "target": target_draws if target_draws is not None else auto_target,
            "auto_target": auto_target,
            "final_draws": final_draws,
            "expected_draws": round(sum(float(row.get("fair_probabilities", {}).get("draw", 0.0)) for row in ok_rows), 3),
        },
        "source_status": source.get("source_status"),
        "rows": final_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# KickTipp leverage tip sheet",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Mode: **{report['mode']}**. Draw budget: **{report['draw_budget']['final_draws']}/{report['draw_budget']['target']}** selected; market expected draws `{report['draw_budget']['expected_draws']}`.",
        "",
        "This sheet optimizes the private league: EV first, then leverage against expected friend chalk and leader correlation. Not betting advice, not LLM scoreline cosplay.",
        "",
        "## Put these in",
        "",
        "| Kickoff UTC | Match | Final | EV pick | Leverage | Anti-leader | Gain≥2 | Loss≥2 | Reason |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        if row.get("status") != "ok":
            lines.append(f"| {row.get('kickoff_utc')} | {row.get('match')} | — | — | — | — | — | — | {row.get('reason')} |")
            continue
        final = row["final_pick"]
        ev = row["ev_pick"]
        lev = row["leverage_pick"]
        anti = row["anti_leader_pick"]
        lines.append(
            f"| {row['kickoff_utc']} | {row['match']} | **{final['scoreline']}** | {ev['scoreline']} | {lev['scoreline']} | {anti['scoreline']} | "
            f"{final['p_gain_2plus']:.1%} | {final['p_loss_2plus']:.1%} | {row['selection_reason']} |"
        )
    lines += ["", "## Match evidence", ""]
    for row in report["rows"]:
        lines.append(f"### {row.get('match')}")
        if row.get("status") != "ok":
            lines.append(f"- {row.get('reason')}")
            lines.append("")
            continue
        final = row["final_pick"]
        fair = row["fair_probabilities"]
        lines.append(
            f"- Final **{final['scoreline']}** ({final['pick']}), EV {final['expected_points']:.2f}, edge vs field {final['edge_vs_field']:.2f}, edge vs leaders {final['edge_vs_leaders']:.2f}."
        )
        lines.append(
            f"- Fair 1/X/2: {fair['home']:.1%}/{fair['draw']:.1%}/{fair['away']:.1%}; field estimate: {', '.join(row.get('estimated_field_predictions') or [])}; leaders: {', '.join(row.get('estimated_leader_predictions') or [])}."
        )
        lines.append(f"- Baseline EV/draw-trap pick: {row.get('baseline_tip')} — {row.get('baseline_reason')}.")
        if row.get("draw_budget_adjusted"):
            lines.append(f"- Slate adjustment: pre-budget pick was {row.get('pre_budget_pick', {}).get('scoreline')}.")
        alternatives = ", ".join(f"{c['scoreline']} EV {c['expected_points']:.2f} edge {c['edge_vs_field']:.2f}" for c in row.get("top_candidates", [])[:5])
        lines.append(f"- Top composite candidates: {alternatives}.")
        if row.get("source_risk_flags"):
            lines.append("- Source flags: " + ", ".join(row["source_risk_flags"]))
        headlines = row.get("news") or []
        if headlines:
            lines.append("- News: " + " | ".join(headlines[:2]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def compact_output(report: dict[str, Any]) -> str:
    rows = [row for row in report["rows"] if row.get("status") == "ok"]
    if not rows:
        return "No usable leverage tips — odds missing."
    return "\n".join(f"{row['match']}: {row['final_pick']['scoreline']} ({row['mode']}, gain≥2 {row['final_pick']['p_gain_2plus']:.1%}, loss≥2 {row['final_pick']['p_loss_2plus']:.1%})" for row in rows)


def main() -> int:
    args = build_parser().parse_args()
    report = build_leverage_sheet(
        days=args.days,
        date=args.date,
        include_started=args.include_started,
        hours=args.hours,
        weather=not args.no_weather,
        context_path=args.context,
        mode_override=args.mode,
        target_draws=args.target_draws,
    )
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
            "mode": report["mode"],
            "draw_budget": report["draw_budget"],
            "tips": [{"match": row.get("match"), "final": (row.get("final_pick") or {}).get("scoreline"), "status": row.get("status")} for row in report["rows"]],
            "json_out": display_path(json_path),
            "markdown_out": display_path(md_path),
        }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
