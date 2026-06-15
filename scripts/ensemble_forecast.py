#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.data import read_csv
from worldcup_predictor.ensemble import build_ensemble_report, load_ensemble_config
from worldcup_predictor.paths import DATA_DIR
from worldcup_predictor.predictions import load_prediction_store
from worldcup_predictor.scoring import score_store

DEFAULT_CONFIG_PATH = ROOT / "config" / "ensemble_models.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build weighted and calibrated ensemble forecasts from saved predictions.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to ensemble config JSON.")
    parser.add_argument("--json-out", default="reports/ensemble_forecast.json")
    parser.add_argument("--markdown-out", default="reports/ensemble_forecast.md")
    parser.add_argument("--no-score", action="store_true", help="Do not recompute in-memory prediction scores before ensemble evaluation.")
    return parser


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Ensemble forecast", ""]
    backtest = report["backtest"]
    lines += [
        "## Backtest comparison",
        "",
        "| Method | Correct | Rate |",
        "|---|---:|---:|",
        f"| Raw consensus | {backtest['raw_consensus_correct']}/{backtest['matches']} | {backtest['raw_consensus_rate']:.3f} |",
        f"| Weighted consensus | {backtest['weighted_consensus_correct']}/{backtest['matches']} | {backtest['weighted_consensus_rate']:.3f} |",
        f"| Calibrated pick | {backtest['calibrated_correct']}/{backtest['matches']} | {backtest['calibrated_rate']:.3f} |",
        "",
        "## Model weights",
        "",
        f"Required completed matches: `{report['model_weights']['required_matches']}`",
        "",
        "| Model | Matches | Avg pts | Weight |",
        "|---|---:|---:|---:|",
    ]
    for row in report["model_weights"]["models"]:
        lines.append(f"| {row['model_alias']} | {row['matches']} | {row['average_points']:.2f} | {row['weight']:.4f} |")

    lines += ["", "## Backtest rows", "", "| ID | Match | Actual | Raw | Weighted | Calibrated | Flags |", "|---:|---|---|---|---|---|---|"]
    for row in report["backtest_rows"]:
        flags = ", ".join(row["risk_flags"]) or "—"
        lines.append(
            f"| {row['match_id']} | {row['match']} | {row['actual_winner']} {row['actual_score']} | "
            f"{row['raw_consensus']} | {row['weighted_consensus']} | {row['calibrated_pick']} | {flags} |"
        )

    lines += ["", "## Upcoming / unscored forecasts", "", "| ID | Match | Kickoff UTC | Pick | Confidence | Raw | Weighted | Flags |", "|---:|---|---|---|---:|---|---|---|"]
    for row in report["forecasts"]:
        flags = ", ".join(row["risk_flags"]) or "—"
        lines.append(
            f"| {row['match_id']} | {row['match']} | {row.get('kickoff_utc') or ''} | "
            f"{row['calibrated_pick']} | {row['calibrated_confidence']:.3f} | "
            f"{row['raw_consensus']} | {row['weighted_consensus']} | {flags} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    config = load_ensemble_config(config_path)
    store = load_prediction_store()
    if not args.no_score:
        score_store(store)
    schedule = read_csv(DATA_DIR / "schedule_2026.csv")
    report = build_ensemble_report(store, schedule, config)

    json_path = Path(args.json_out)
    md_path = Path(args.markdown_out)
    if not json_path.is_absolute():
        json_path = ROOT / json_path
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(json.dumps({
        "backtest": report["backtest"],
        "forecast_count": len(report["forecasts"]),
        "weighted_models": [row["model_alias"] for row in report["model_weights"]["models"]],
        "json_out": display_path(json_path),
        "markdown_out": display_path(md_path),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
