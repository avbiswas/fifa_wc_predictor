from __future__ import annotations


def extract_lm_usage(lm) -> dict:
    history = getattr(lm, "history", []) or []
    calls = [extract_call_usage(call) for call in history]
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost": 0.0}

    for call in calls:
        usage = call.get("usage") or {}
        totals["prompt_tokens"] += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        totals["completion_tokens"] += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        totals["total_tokens"] += int(usage.get("total_tokens") or 0)
        totals["cost"] += float(call.get("cost") or usage.get("cost") or 0.0)

    if totals["total_tokens"] == 0:
        totals["total_tokens"] = totals["prompt_tokens"] + totals["completion_tokens"]

    return {"totals": totals, "calls": calls}


def extract_call_usage(call: dict) -> dict:
    response = call.get("response") or {}
    usage = call.get("usage") or response.get("usage") or {}
    return {
        "model": call.get("model"),
        "usage": normalize_usage(usage),
        "cost": call.get("cost") or response.get("cost"),
    }


def normalize_usage(usage) -> dict:
    if not isinstance(usage, dict):
        return {}
    return {
        key: value
        for key, value in usage.items()
        if key in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens", "cost"}
    }
