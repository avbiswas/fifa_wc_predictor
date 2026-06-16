from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from worldcup_predictor.leverage_optimizer import parse_scoreline

ARCHIVE_FORMAT_VERSION = 1


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def safe_slug(value: str, *, fallback: str = "unknown") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def safe_timestamp(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "-", value).strip("-")


def record_event_key(row: dict[str, Any]) -> str:
    event_id = row.get("event_id")
    if event_id not in {None, "", "None"}:
        return f"event-{event_id}"
    match = str(row.get("match") or "unknown-match")
    kickoff = str(row.get("kickoff_utc") or "unknown-kickoff")
    return f"match-{safe_slug(match)}-{safe_slug(kickoff)}"


def is_pre_kickoff(generated_at: str | None, kickoff_utc: str | None) -> bool:
    generated = parse_datetime(generated_at)
    kickoff = parse_datetime(kickoff_utc)
    if generated is None or kickoff is None:
        return False
    return generated <= kickoff


def archive_record_from_row(report: dict[str, Any], row: dict[str, Any], *, snapshot_id: str) -> dict[str, Any]:
    final_pick = row.get("final_pick") or {}
    generated_at = report.get("generated_at")
    return {
        "archive_format_version": ARCHIVE_FORMAT_VERSION,
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "event_id": row.get("event_id"),
        "event_key": record_event_key(row),
        "kickoff_utc": row.get("kickoff_utc"),
        "match": row.get("match"),
        "home": row.get("home"),
        "away": row.get("away"),
        "mode": row.get("mode") or report.get("mode"),
        "final_tip": final_pick.get("scoreline"),
        "final_pick": final_pick,
        "eligible_for_backtest": bool(final_pick.get("scoreline")) and is_pre_kickoff(generated_at, row.get("kickoff_utc")),
        "draw_budget": report.get("draw_budget"),
        "current_state": report.get("current_state"),
        "rules": report.get("rules"),
        "source_status": report.get("source_status"),
        "row": row,
    }


def archive_leverage_report(report: dict[str, Any], archive_dir: str | Path) -> dict[str, Any]:
    """Persist an immutable leverage-sheet snapshot plus JSONL pick records.

    The latest report files under reports/ are overwritten on every run; this archive is
    append-only enough for real backtests once actual scorelines arrive.
    """
    root = Path(archive_dir)
    generated_at = str(report.get("generated_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    snapshot_id = safe_timestamp(generated_at)
    day = generated_at[:10] if re.match(r"\d{4}-\d{2}-\d{2}", generated_at) else "unknown-date"

    reports_dir = root / "reports" / day
    latest_dir = root / "latest_by_event"
    reports_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = reports_dir / f"{snapshot_id}.json"
    snapshot_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    records = [
        archive_record_from_row(report, row, snapshot_id=snapshot_id)
        for row in report.get("rows", [])
        if row.get("status") == "ok" and (row.get("final_pick") or {}).get("scoreline")
    ]

    ledger_path = root / "picks.jsonl"
    with ledger_path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            if record.get("eligible_for_backtest"):
                (latest_dir / f"{record['event_key']}.json").write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    return {
        "snapshot_id": snapshot_id,
        "snapshot_path": str(snapshot_path),
        "ledger_path": str(ledger_path),
        "records_written": len(records),
        "eligible_records": sum(1 for record in records if record.get("eligible_for_backtest")),
    }


def load_pick_ledger(archive_dir: str | Path) -> list[dict[str, Any]]:
    ledger_path = Path(archive_dir) / "picks.jsonl"
    if not ledger_path.exists():
        return []
    records: list[dict[str, Any]] = []
    with ledger_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def latest_archived_picks(archive_dir: str | Path) -> dict[str, dict[str, Any]]:
    """Return latest pre-kickoff archived pick per event key."""
    latest: dict[str, dict[str, Any]] = {}
    for record in load_pick_ledger(archive_dir):
        if not record.get("eligible_for_backtest") or not record.get("final_tip"):
            continue
        key = str(record.get("event_key") or "")
        if not key:
            continue
        previous = latest.get(key)
        if previous is None or str(record.get("generated_at") or "") >= str(previous.get("generated_at") or ""):
            latest[key] = record
    return latest


def scoreline_from_archived_record(record: dict[str, Any]) -> tuple[int, int]:
    return parse_scoreline(str(record["final_tip"]))
