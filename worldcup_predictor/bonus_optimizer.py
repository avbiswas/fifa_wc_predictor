from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BonusOption:
    label: str
    probability: float
    ownership: float = 0.0
    category: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class BonusSelection:
    label: str
    probability: float
    ownership: float
    category: str | None
    score: float
    expected_points: float
    leverage_value: float
    reason: str


MODE_LEVERAGE_WEIGHT = {
    "safe": 0.15,
    "balanced": 0.35,
    "controlled_attack": 0.55,
    "desperation": 0.95,
    "protect_spieltag_win": 0.05,
}


def clamp_probability(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number > 1:
        number = number / 100
    return max(0.0, min(1.0, number))


def parse_options(raw_options: list[dict[str, Any]]) -> list[BonusOption]:
    options = []
    for row in raw_options:
        label = row.get("label") or row.get("team") or row.get("answer")
        if not label:
            continue
        options.append(
            BonusOption(
                label=str(label),
                probability=clamp_probability(row.get("probability"), 0.0),
                ownership=clamp_probability(row.get("ownership"), 0.0),
                category=row.get("category"),
                notes=row.get("notes"),
            )
        )
    return options


def option_score(option: BonusOption, *, points: int = 4, mode: str = "controlled_attack") -> BonusSelection:
    leverage_weight = MODE_LEVERAGE_WEIGHT.get(mode, MODE_LEVERAGE_WEIGHT["controlled_attack"])
    expected_points = points * option.probability
    # If friends are crowded on an answer, it still scores but does not separate us.
    # probability*(1-ownership) is the useful catch-up component.
    leverage_value = points * option.probability * (1 - option.ownership)
    score = expected_points + leverage_weight * leverage_value
    if option.ownership >= 0.75:
        reason = "high probability but crowded"
    elif option.probability >= 0.22 and option.ownership <= 0.35:
        reason = "smart lower-owned upside"
    else:
        reason = "probability/leverage blend"
    return BonusSelection(
        label=option.label,
        probability=option.probability,
        ownership=option.ownership,
        category=option.category,
        score=score,
        expected_points=expected_points,
        leverage_value=leverage_value,
        reason=reason,
    )


def select_bonus_answers(
    options: list[BonusOption],
    *,
    slots: int,
    points: int = 4,
    mode: str = "controlled_attack",
    contrarian_slots: int | None = None,
) -> list[BonusSelection]:
    if slots <= 0 or not options:
        return []
    scored = [option_score(option, points=points, mode=mode) for option in options]
    if contrarian_slots is None:
        if mode in {"safe", "protect_spieltag_win"}:
            contrarian_slots = 0
        elif mode == "desperation" and slots >= 2:
            contrarian_slots = max(1, slots // 3)
        elif slots >= 4:
            contrarian_slots = max(1, slots // 4)
        else:
            contrarian_slots = 0
    contrarian_slots = max(0, min(slots, contrarian_slots))

    selected: list[BonusSelection] = []
    seen: set[str] = set()

    contrarian_pool = sorted(
        [row for row in scored if row.ownership <= 0.45 and row.probability >= 0.08],
        key=lambda row: (row.leverage_value, row.probability),
        reverse=True,
    )
    for row in contrarian_pool[:contrarian_slots]:
        selected.append(row)
        seen.add(row.label)

    main_pool = sorted(scored, key=lambda row: (row.score, row.probability), reverse=True)
    for row in main_pool:
        if row.label in seen:
            continue
        selected.append(row)
        seen.add(row.label)
        if len(selected) >= slots:
            break
    return selected[:slots]


def optimize_bonus_questions(context: dict[str, Any], *, mode: str = "controlled_attack") -> dict[str, Any]:
    reports = []
    for question in context.get("questions", []):
        options = parse_options(question.get("options") or [])
        slots = int(question.get("slots") or question.get("answers") or 1)
        points = int(question.get("points") or context.get("default_points") or 4)
        q_mode = question.get("mode") or mode
        selected = select_bonus_answers(
            options,
            slots=slots,
            points=points,
            mode=q_mode,
            contrarian_slots=question.get("contrarian_slots"),
        )
        reports.append(
            {
                "id": question.get("id"),
                "question": question.get("question") or question.get("label"),
                "mode": q_mode,
                "slots": slots,
                "points": points,
                "selected": [selection_to_dict(row) for row in selected],
                "ranked_options": [selection_to_dict(row) for row in sorted([option_score(o, points=points, mode=q_mode) for o in options], key=lambda r: r.score, reverse=True)],
                "status": "ok" if options else "missing_options",
            }
        )
    return {
        "strategy": "bonus questions are set picks: mostly probability, with one or two lower-owned answers when catching up",
        "mode": mode,
        "questions": reports,
    }


def selection_to_dict(selection: BonusSelection) -> dict[str, Any]:
    data = asdict(selection)
    for key in ["probability", "ownership", "score", "expected_points", "leverage_value"]:
        data[key] = round(float(data[key]), 4)
    return data


def load_bonus_context(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
