#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_leverage_tip_sheet import build_leverage_sheet, default_context_path, render_markdown  # noqa: E402
from worldcup_predictor.kicktipp_archive import archive_leverage_report  # noqa: E402

STATE_PATH = ROOT / "reports" / "kicktipp_watchdog_state.json"
JSON_OUT = ROOT / "reports" / "tip_sheet_watchdog.json"
MD_OUT = ROOT / "reports" / "tip_sheet_watchdog.md"
ARCHIVE_DIR = ROOT / "data" / "kicktipp" / "archive"
LOCAL_TZ = ZoneInfo("Europe/Berlin")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Silent-unless-useful KickTipp exploit-engine watchdog for Hermes cron.")
    parser.add_argument("--mode", choices=["watch", "daily", "first-game-brief"], default="watch")
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


def human_badges(row: dict[str, Any]) -> str:
    final = row.get("final_pick") or {}
    flags = set(row.get("source_risk_flags") or [])
    gain = float(final.get("p_gain_2plus", 0) or 0)
    badges = []
    if "draw_trap" in flags:
        badges.append("🪤 draw trap")
    if "wet_weather" in flags:
        badges.append("🌧️ weather chaos")
    if any(flag.startswith("big_") for flag in flags):
        badges.append("📈 market moved")
    if gain >= 0.20:
        badges.append("🚀 real swing chance")
    elif gain >= 0.10:
        badges.append("⚡ small swing chance")
    if not badges and "low_edge" in flags:
        badges.append("🧊 thin edge, keep it clean")
    if not badges:
        badges.append("✅ straight pick")
    return " · ".join(dict.fromkeys(badges))


def format_tip_line(row: dict[str, Any], *, with_time: bool = True) -> str:
    final = row.get("final_pick") or {}
    kickoff = ""
    if with_time and row.get("kickoff_utc"):
        kickoff = parse_dt(row["kickoff_utc"]).astimezone(LOCAL_TZ).strftime("%H:%M · ")
    return f"• {kickoff}{row['match']}: **{final.get('scoreline')}**  _{human_badges(row)}_"


def compact_rows(rows: list[dict[str, Any]], *, limit: int = 8) -> str:
    usable = [row for row in rows if row.get("status") == "ok"][:limit]
    if not usable:
        return "No usable tips yet — odds are missing. Annoying, but better than guessing."
    return "\n".join(format_tip_line(row) for row in usable)


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


def future_rows(rows: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    usable = []
    for row in rows:
        if row.get("status") != "ok" or not row.get("kickoff_utc"):
            continue
        kickoff = parse_dt(row["kickoff_utc"])
        if kickoff >= now:
            usable.append(row)
    return sorted(usable, key=lambda row: parse_dt(row["kickoff_utc"]))


def slate_rows(rows: list[dict[str, Any]], first_kickoff: datetime, *, slate_hours: float = 16) -> list[dict[str, Any]]:
    slate_end = first_kickoff + timedelta(hours=slate_hours)
    return [
        row
        for row in future_rows(rows, first_kickoff)
        if first_kickoff <= parse_dt(row["kickoff_utc"]) <= slate_end
    ]


def render_first_game_brief(rows: list[dict[str, Any]], first_kickoff: datetime) -> str:
    local_first = first_kickoff.astimezone(LOCAL_TZ)
    draw_traps = sum(1 for row in rows if "draw_trap" in set(row.get("source_risk_flags") or []))
    lines = [
        "🏆 KickTipp slate incoming",
        f"First kickoff: **{local_first:%H:%M}**. We’re in controlled attack: press smart, don’t go full casino.",
        "",
    ]
    lines.extend(format_tip_line(row) for row in rows)
    if draw_traps:
        noun = "trap" if draw_traps == 1 else "traps"
        lines.extend(["", f"🧠 {draw_traps} draw {noun} on the card. That’s where we can steal points if the room stays favorite-happy."])
    return "\n".join(lines)


def first_game_brief(rows: list[dict[str, Any]], state: dict[str, Any], *, alert_window_hours: float, digest: str, now: datetime) -> str | None:
    upcoming = future_rows(rows, now)
    if not upcoming:
        state["last_digest"] = digest
        state["last_run_at"] = now.isoformat().replace("+00:00", "Z")
        return None

    first = upcoming[0]
    first_kickoff = parse_dt(first["kickoff_utc"])
    hours_until = (first_kickoff - now).total_seconds() / 3600
    brief_key = first_kickoff.astimezone(LOCAL_TZ).date().isoformat()

    briefed_dates = state.get("briefed_dates", {})
    if not isinstance(briefed_dates, dict):
        briefed_dates = {}

    state["last_digest"] = digest
    state["last_run_at"] = now.isoformat().replace("+00:00", "Z")
    state["briefed_dates"] = {
        key: value
        for key, value in briefed_dates.items()
        if key >= (now.astimezone(LOCAL_TZ).date() - timedelta(days=14)).isoformat()
    }

    if not (0 <= hours_until <= alert_window_hours):
        return None
    if state["briefed_dates"].get(brief_key):
        return None

    slate = slate_rows(rows, first_kickoff, slate_hours=16)
    state["briefed_dates"][brief_key] = {
        "sent_at": now.isoformat().replace("+00:00", "Z"),
        "first_event_id": first.get("event_id"),
        "digest": digest,
    }
    return render_first_game_brief(slate, first_kickoff)


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
        print("🏆 KickTipp sheet ready\n\n" + compact_rows(rows, limit=12))
        return 0

    if args.mode == "first-game-brief":
        message = first_game_brief(
            rows,
            state,
            alert_window_hours=args.alert_window_hours,
            digest=digest,
            now=datetime.now(timezone.utc),
        )
        save_state(state)
        if message:
            print(message)
        return 0

    messages = []
    if state.get("last_digest") and state.get("last_digest") != digest:
        messages.append("📈 KickTipp sheet changed\n\n" + compact_rows(rows, limit=10))
    elif not state.get("last_digest"):
        messages.append("🟢 KickTipp engine armed\n\n" + compact_rows(rows, limit=10))

    alerted = state.get("alerted", {})
    for row in due_rows(rows, args.alert_window_hours):
        final = row.get("final_pick") or {}
        key = f"{row.get('event_id')}:{final.get('scoreline')}"
        if alerted.get(key):
            continue
        messages.append(f"⏰ Kickoff soon: {row['match']} — enter **{final.get('scoreline')}**")
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
