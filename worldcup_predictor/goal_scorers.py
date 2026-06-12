from __future__ import annotations


def normalize_goal_scorers(value: object, limit: int = 3) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:limit]
    if not isinstance(value, str):
        return []

    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for character in value:
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        if character in ",;" and depth == 0:
            item = "".join(current).strip()
            if item:
                parts.append(item)
            current = []
            continue
        current.append(character)
    item = "".join(current).strip()
    if item:
        parts.append(item)

    scorers = []
    for part in parts:
        if ":" in part:
            prefix, candidate = part.split(":", 1)
            if len(prefix.split()) <= 3:
                part = candidate.strip()
        if part and not part.startswith("("):
            scorers.append(part)
    return scorers[:limit]
