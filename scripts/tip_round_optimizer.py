#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.tip_optimizer import Odds, ScoreRules, draw_guard_tip, fair_probabilities, score_tip

SCREENSHOT_SAMPLE = [
    {
        "match": "Deutschland vs Curaçao",
        "odds": Odds(1.05, 17.0, 51.0),
        "tool_score": (3, 0),
        "actual": (7, 1),
    },
    {
        "match": "Niederlande vs Japan",
        "odds": Odds(2.00, 3.50, 3.70),
        "tool_score": (2, 1),
        "actual": (2, 2),
    },
    {
        "match": "Elfenbeinküste vs Ecuador",
        "odds": Odds(3.25, 2.90, 2.45),
        "tool_score": (0, 3),
        "actual": (1, 0),
    },
    {
        "match": "Schweden vs Tunesien",
        "odds": Odds(1.87, 3.40, 4.50),
        "tool_score": (2, 1),
        "actual": (5, 1),
    },
    {
        "match": "Spanien vs Kap Verde",
        "odds": Odds(1.10, 10.5, 23.0),
        "tool_score": (3, 0),
        "actual": (0, 0),
    },
    {
        "match": "Belgien vs Ägypten",
        "odds": Odds(1.53, 4.20, 6.00),
        "tool_score": (2, 1),
        "actual": (1, 1),
    },
    {
        "match": "Saudi-Arabien vs Uruguay",
        "odds": Odds(7.00, 4.10, 1.49),
        "tool_score": (1, 2),
        "actual": (1, 1),
    },
    {
        "match": "Iran vs Neuseeland",
        "odds": Odds(1.80, 3.40, 4.80),
        "tool_score": (0, 3),
        "actual": (2, 2),
    },
]


def outcome(score: tuple[int, int]) -> str:
    if score[0] > score[1]:
        return "home"
    if score[1] > score[0]:
        return "away"
    return "draw"


def main() -> int:
    rules = ScoreRules()
    rows = []
    tool_points = 0
    optimizer_points = 0
    tool_correct = 0
    optimizer_correct = 0
    for item in SCREENSHOT_SAMPLE:
        tip = draw_guard_tip(item["odds"])
        optimized = (tip.home_goals, tip.away_goals)
        tool_score = item["tool_score"]
        actual = item["actual"]
        tool_row_points = score_tip(tool_score, actual, rules)
        optimizer_row_points = score_tip(optimized, actual, rules)
        tool_points += tool_row_points
        optimizer_points += optimizer_row_points
        tool_correct += outcome(tool_score) == outcome(actual)
        optimizer_correct += outcome(optimized) == outcome(actual)
        rows.append(
            {
                "match": item["match"],
                "odds": {
                    "home": item["odds"].home,
                    "draw": item["odds"].draw,
                    "away": item["odds"].away,
                },
                "fair_probabilities": {key: round(value, 4) for key, value in fair_probabilities(item["odds"]).items()},
                "tool_score": f"{tool_score[0]}:{tool_score[1]}",
                "optimizer_score": tip.scoreline,
                "optimizer_reason": tip.reason,
                "actual": f"{actual[0]}:{actual[1]}",
                "tool_points": tool_row_points,
                "optimizer_points": optimizer_row_points,
            }
        )

    report = {
        "rules": {"exact": rules.exact, "goal_difference": rules.goal_difference, "tendency": rules.tendency},
        "summary": {
            "matches": len(rows),
            "tool_points": tool_points,
            "optimizer_points": optimizer_points,
            "tool_outcomes_correct": tool_correct,
            "optimizer_outcomes_correct": optimizer_correct,
        },
        "rows": rows,
    }
    out_json = ROOT / "reports" / "tip_round_optimizer_screenshot.json"
    out_md = ROOT / "reports" / "tip_round_optimizer_screenshot.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Tip round optimizer backtest",
        "",
        "Default scoring assumed: exact=4, win goal difference=3, tendency=2. Non-exact draws get 2 because the rule table has no draw goal-difference bonus.",
        "",
        "| Strategy | Outcome hits | Points |",
        "|---|---:|---:|",
        f"| Tool scores | {tool_correct}/{len(rows)} | {tool_points} |",
        f"| Odds draw-guard | {optimizer_correct}/{len(rows)} | {optimizer_points} |",
        "",
        "| Match | Actual | Tool | Optimizer | Tool pts | Opt pts | Reason |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['match']} | {row['actual']} | {row['tool_score']} | {row['optimizer_score']} | "
            f"{row['tool_points']} | {row['optimizer_points']} | {row['optimizer_reason']} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "json_out": str(out_json.relative_to(ROOT)), "markdown_out": str(out_md.relative_to(ROOT))}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
