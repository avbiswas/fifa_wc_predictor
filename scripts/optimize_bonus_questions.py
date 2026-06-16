#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.bonus_optimizer import load_bonus_context, optimize_bonus_questions  # noqa: E402
from worldcup_predictor.leverage_optimizer import MODE_WEIGHTS  # noqa: E402

DEFAULT_CONTEXT = ROOT / "data" / "kicktipp" / "bonus_questions.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimize KickTipp bonus-question answers as set picks with probability + ownership leverage.")
    parser.add_argument("--context", default=str(DEFAULT_CONTEXT))
    parser.add_argument("--mode", choices=sorted(MODE_WEIGHTS), default="controlled_attack")
    parser.add_argument("--json-out", default="reports/bonus_question_optimizer.json")
    parser.add_argument("--markdown-out", default="reports/bonus_question_optimizer.md")
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


def render_markdown(report: dict) -> str:
    lines = [
        "# KickTipp bonus-question optimizer",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Mode: **{report['mode']}**",
        "",
        "Bonus questions are set picks. Take mostly the best probabilities, but reserve lower-owned slots when we need catch-up leverage.",
        "",
    ]
    if not report.get("questions"):
        lines += [
            "No bonus questions/options entered yet.",
            "",
            "Fill `data/kicktipp/bonus_questions.json` with real options: label, probability, ownership, slots, points.",
        ]
        return "\n".join(lines).rstrip() + "\n"

    for question in report["questions"]:
        lines += [
            f"## {question.get('question') or question.get('id')}",
            "",
            f"Status: `{question['status']}`, slots: `{question['slots']}`, points each: `{question['points']}`",
            "",
            "### Selected",
            "",
            "| Answer | Prob | Own | Exp pts | Lev value | Reason |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for row in question.get("selected", []):
            lines.append(
                f"| {row['label']} | {row['probability']:.1%} | {row['ownership']:.1%} | {row['expected_points']:.2f} | {row['leverage_value']:.2f} | {row['reason']} |"
            )
        lines += ["", "### Ranked options", "", "| Answer | Score | Prob | Own |", "|---|---:|---:|---:|"]
        for row in question.get("ranked_options", [])[:20]:
            lines.append(f"| {row['label']} | {row['score']:.2f} | {row['probability']:.1%} | {row['ownership']:.1%} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = build_parser().parse_args()
    context = load_bonus_context(args.context)
    optimized = optimize_bonus_questions(context, mode=args.mode)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "context_path": args.context,
        **optimized,
    }
    json_path = resolve_output_path(args.json_out)
    md_path = resolve_output_path(args.markdown_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "questions": len(report.get("questions", [])),
        "selected": sum(len(q.get("selected", [])) for q in report.get("questions", [])),
        "json_out": display_path(json_path),
        "markdown_out": display_path(md_path),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
