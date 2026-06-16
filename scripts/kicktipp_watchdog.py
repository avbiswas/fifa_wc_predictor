#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_leverage_tip_sheet import build_leverage_sheet, default_context_path, render_markdown  # noqa: E402
from worldcup_predictor.kicktipp_archive import archive_leverage_report  # noqa: E402

STATE_PATH = ROOT / "reports" / "kicktipp_watchdog_state.json"
JSON_OUT = ROOT / "reports" / "tip_sheet_watchdog.json"
MD_OUT = ROOT / "reports" / "tip_sheet_watchdog.md"
ARCHIVE_DIR = ROOT / "data" / "kicktipp" / "archive"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Silent-unless-useful KickTipp exploit-engine watchdog for Hermes cron.")
    parser.add_argument("--mode", choices=["watch", "daily"], default="watch")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--hours", type=float, default=36)
    parser.add_argument("--alert-window-hours", type=float, default=2.25)
    parser.add_argument("--no-weather", action="store_true")
    parser.add_argument("--context", default=str(default_context_path()))
    parser.add_argument("--leverage-mode", help="Override mode from the KickTipp context, e.g. controlled_attack/desperation.")
    return parser


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest_rows(rows: list[dict[str, Any]]) -> str:
    payload = [
        {
            "event_id": row.get("event_id"),
            "kickoff": row.get("kickoff_utc"),
            "match": row.get("match"),
            "tip": (row.get("final_pick") or {}).get("scoreline"),
            "mode": row.get("mode"),
            "odds": row.get("odds_decimal"),
            "flags": row.get("source_risk_flags"),
        }
        for row in rows
        if row.get("status") == "ok"
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def compact_rows(rows: list[dict[str, Any]], *, limit: int = 8) -> str:
    usable = [row for row in rows if row.get("status") == "ok"][:limit]
    if not usable:
        return "No usable tips — odds missing."
    lines = []
    for row in usable:
        final = row.get("final_pick") or {}
        flags = ",".join(row.get("source_risk_flags") or [])
        suffix = f" [{flags}]" if flags else ""
        lines.append(f"{row['match']}: {final.get('scoreline')} ({row.get('mode')}, gain≥2 {float(final.get('p_gain_2plus', 0)):.1%}){suffix}")
    return "\n".join(lines)


def due_rows(rows: list[dict[str, Any]], alert_window_hours: float) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    due = []
    for row in rows:
        if row.get("status") != "ok" or not row.get("kickoff_utc"):
            continue
        hours = (parse_dt(row["kickoff_utc"]) - now).total_seconds() / 3600
        if 0 <= hours <= alert_window_hours:
            due.append(row)
    return due


def main() -> int:
    args = build_parser().parse_args()
    report = build_leverage_sheet(
        days=args.days,
        date=None,
        include_started=False,
        hours=args.hours,
        weather=not args.no_weather,
        context_path=args.context,
        mode_override=args.leverage_mode,
    )
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(report), encoding="utf-8")
    archive_leverage_report(report, ARCHIVE_DIR)

    rows = report.get("rows", [])
    state = load_state()
    digest = digest_rows(rows)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if args.mode == "daily":
        state["last_daily_at"] = now
        state["last_digest"] = digest
        save_state(state)
        print("KickTipp sheet ready:\n" + compact_rows(rows, limit=12))
        return 0

    messages = []
    if state.get("last_digest") and state.get("last_digest") != digest:
        messages.append("Odds/tips changed:\n" + compact_rows(rows, limit=10))
    elif not state.get("last_digest"):
        messages.append("KickTipp exploit engine armed:\n" + compact_rows(rows, limit=10))

    alerted = state.get("alerted", {})
    for row in due_rows(rows, args.alert_window_hours):
        final = row.get("final_pick") or {}
        key = f"{row.get('event_id')}:{final.get('scoreline')}"
        if alerted.get(key):
            continue
        messages.append(f"Kickoff soon — enter this: {row['match']} **{final.get('scoreline')}** ({row.get('mode')}, gain≥2 {float(final.get('p_gain_2plus', 0)):.1%})")
        alerted[key] = now

    state["last_digest"] = digest
    state["last_run_at"] = now
    state["alerted"] = alerted
    save_state(state)

    if messages:
        print("\n\n".join(messages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
