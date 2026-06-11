from __future__ import annotations

import json
import urllib.request

from .paths import MODEL, MODEL_REGISTRY_PATH


def load_model_registry() -> dict:
    if not MODEL_REGISTRY_PATH.exists():
        return {"default": MODEL, "models": {}}
    return json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))


def competition_aliases() -> list[str]:
    registry = load_model_registry()
    return list(registry.get("models", {}).keys())


def default_model_alias() -> str:
    registry = load_model_registry()
    return registry.get("default") or MODEL


def resolve_model(model_or_alias: str | None) -> tuple[str, str]:
    registry = load_model_registry()
    model_key = model_or_alias or registry.get("default") or MODEL
    models = registry.get("models", {})
    value = models.get(model_key)
    if isinstance(value, dict):
        return model_key, value["model"]
    return model_key, value or model_key


def model_registry_rows() -> list[dict[str, str]]:
    registry = load_model_registry()
    rows = []
    for alias, value in registry.get("models", {}).items():
        if isinstance(value, dict):
            rows.append({"alias": alias, **value})
        else:
            rows.append({"alias": alias, "model": value})
    return rows


def validate_openrouter_models() -> list[dict[str, str | bool]]:
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        available = {model["id"] for model in json.load(response).get("data", [])}

    rows = []
    for row in model_registry_rows():
        model = row["model"]
        openrouter_id = model.removeprefix("openrouter/")
        rows.append({**row, "available": openrouter_id in available or openrouter_id.startswith("~")})
    return rows
