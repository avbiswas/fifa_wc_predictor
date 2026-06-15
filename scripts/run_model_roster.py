#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config" / "ensemble_models.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the configured Hermes model roster for upcoming fixtures.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to ensemble config JSON with hermes_roster.")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--tz", default="Europe/Berlin")
    parser.add_argument("--future-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def load_roster(path: Path) -> list[dict[str, Any]]:
    config = json.loads(path.read_text(encoding="utf-8"))
    roster = config.get("hermes_roster") or []
    if not isinstance(roster, list):
        raise SystemExit("hermes_roster must be a list")
    normalized = roster or [{"provider": None, "model": None}]
    for index, item in enumerate(normalized, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"hermes_roster item {index} must be an object")
    return normalized


def command_for(args: argparse.Namespace, item: dict[str, Any]) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_hermes_predictions.py"),
        "--days",
        str(args.days),
        "--tz",
        args.tz,
    ]
    if args.future_only:
        cmd.append("--future-only")
    if args.force:
        cmd.append("--force")
    if args.dry_run:
        cmd.append("--dry-run")
    model = item.get("model")
    provider = item.get("provider")
    if model:
        cmd += ["--hermes-model", str(model)]
    if provider:
        cmd += ["--hermes-provider", str(provider)]
    return cmd


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    roster = load_roster(config_path)
    commands = [command_for(args, item) for item in roster]
    print(json.dumps({"roster_size": len(roster), "commands": commands}, indent=2, ensure_ascii=False), flush=True)
    for cmd in commands:
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
