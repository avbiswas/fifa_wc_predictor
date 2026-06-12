from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
CACHE_PATH = ROOT / "data" / "cache" / "match_retrieval_cache.json"
PREDICTIONS_PATH = ROOT / "data" / "predictions" / "predictions.json"
STATIC_PREDICTIONS_PATH = ROOT / "cloudflare_app" / "public" / "data" / "predictions.json"
MODEL_REGISTRY_PATH = ROOT / "config" / "competition_models.json"
MODEL = "openrouter/google/gemini-3.5-flash"
