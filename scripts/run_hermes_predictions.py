#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from worldcup_predictor.data import normalize_match_key
from worldcup_predictor.goal_scorers import normalize_goal_scorers
from worldcup_predictor.paths import CACHE_PATH, PREDICTIONS_PATH
from worldcup_predictor.predictions import write_prediction_store
from worldcup_predictor.prepare import prepare_match_data

LEGACY_ALIAS = "hermes-gpt-5.5-codex"
LEGACY_MODEL_NAME = "hermes/openai-codex/gpt-5.5"


@dataclass(frozen=True)
class HermesModelSpec:
    model: str | None
    provider: str | None

    @property
    def alias(self) -> str:
        if not self.model and not self.provider:
            return "hermes-default"
        if not self.model and self.provider:
            return "hermes-" + _slug(f"{self.provider}-default")
        if self.model == "gpt-5.5" and self.provider == "openai-codex":
            return LEGACY_ALIAS
        provider = self.provider or "auto"
        return "hermes-" + _slug(f"{provider}-{self.model}")

    @property
    def stored_model(self) -> str:
        if not self.model and not self.provider:
            return "hermes/default"
        if not self.model and self.provider:
            return f"hermes/{self.provider}/default"
        if self.model == "gpt-5.5" and self.provider == "openai-codex":
            return LEGACY_MODEL_NAME
        provider = self.provider or "auto"
        return f"hermes/{provider}/{self.model}"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Legacy: run match artifacts through local Hermes models for auxiliary forecasts.")
    p.add_argument("--days", type=int, default=3, help="Number of local calendar days starting today.")
    p.add_argument("--tz", default="Europe/Berlin", help="Timezone for today/tomorrow/day-after resolution.")
    p.add_argument("--news-results", type=int, default=5)
    p.add_argument("--force", action="store_true", help="Re-run even if this Hermes alias already exists.")
    p.add_argument("--future-only", action="store_true", help="Skip fixtures whose kickoff has already passed.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--hermes-model",
        action="append",
        default=None,
        help="Hermes model to run. Repeat for a mini-tournament. Default: the configured Hermes model.",
    )
    p.add_argument(
        "--hermes-provider",
        action="append",
        default=None,
        help="Hermes provider to pair with --hermes-model. One value applies to all models; repeated values pair by index. Default: configured Hermes provider.",
    )
    return p


def model_specs(args: argparse.Namespace) -> list[HermesModelSpec]:
    if not args.hermes_model:
        if args.hermes_provider:
            return [HermesModelSpec(model=None, provider=provider or None) for provider in args.hermes_provider]
        return [HermesModelSpec(model=None, provider=None)]
    models = args.hermes_model
    providers = args.hermes_provider or [None]
    if len(providers) == 1:
        providers = providers * len(models)
    if len(providers) != len(models):
        raise SystemExit("Pass either one --hermes-provider or exactly one provider per --hermes-model.")
    return [HermesModelSpec(model=model, provider=(provider or None)) for model, provider in zip(models, providers)]


def schedule_matches(days: int, tz_name: str, future_only: bool) -> list[dict]:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    target_dates = {now.date() + timedelta(days=i) for i in range(days)}
    matches: list[dict] = []
    with (ROOT / "data/processed/schedule_2026.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not (row.get("team1_code") and row.get("team2_code")):
                continue
            kickoff_utc = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
            kickoff_local = kickoff_utc.astimezone(tz)
            if kickoff_local.date() not in target_dates:
                continue
            if future_only and kickoff_local <= now:
                continue
            row["kickoff_local"] = kickoff_local.isoformat()
            row["kickoff_local_human"] = kickoff_local.strftime("%Y-%m-%d %H:%M %Z")
            matches.append(row)
    return sorted(matches, key=lambda r: (r["kickoff_local"], int(r["match_id"])))


def load_store() -> dict:
    if not PREDICTIONS_PATH.exists():
        return {"predictions": []}
    return json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))


def hermes_cmd() -> list[str]:
    configured = os.environ.get("HERMES_BIN")
    if configured:
        path = Path(configured).expanduser()
        if path.exists():
            return [str(path)]
        return [configured]
    discovered = shutil.which("hermes")
    if discovered:
        return [discovered]
    raise SystemExit("Hermes CLI not found")


def extract_json(text: str) -> dict:
    # Hermes quiet mode can print warnings before JSON and session_id after JSON.
    starts = [m.start() for m in re.finditer(r"\{", text)]
    for start in starts:
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : idx + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"No balanced JSON object found in Hermes output: {text[-1000:]}")


def prompt_for(prepared: dict, kickoff_human: str) -> str:
    team1, team2, draw = prepared["choices"]
    payload = {
        "match": prepared["match"],
        "kickoff_local": kickoff_human,
        "choices": [team1, team2, draw],
        "match_context": prepared["model_inputs"]["match_context"],
        "team1_squad": prepared["model_inputs"]["team1_squad"],
        "team2_squad": prepared["model_inputs"]["team2_squad"],
        "recent_record": prepared["model_inputs"].get("recent_record", ""),
        "news_items": prepared["model_inputs"].get("news_items", ""),
        "polymarket_odds": prepared["model_inputs"].get("polymarket_odds", ""),
    }
    return f"""You are the legacy local Hermes forecast runner for the KickTipp exploit engine.
Use only the supplied match artifact. Return one strict JSON object and nothing else.

JSON schema:
{{
  "prediction": "{team1}" | "{team2}" | "Draw",
  "scoreline": "<team name> <goals>-<goals> <team name>",
  "goal_scorers": ["<player> (<team>)", "<player> (<team>)", "<player> (<team>)"],
  "confidence": <number between 0 and 1>,
  "rationale": "one concise evidence-based paragraph",
  "news_summary": "concise bullet-style summary; mention if news search was unavailable"
}}

Hard rules:
- prediction must be exactly one of {team1}, {team2}, Draw.
- goal_scorers must contain exactly three plausible players from the supplied squads when possible.
- Do not call tools. Do not browse. Do not use markdown.

MATCH_ARTIFACT:
{json.dumps(payload, ensure_ascii=False)}
"""


def call_hermes(prompt: str, spec: HermesModelSpec) -> dict:
    cmd = hermes_cmd() + ["chat", "-q", prompt, "--quiet", "--ignore-rules", "--source", "tool", "--max-turns", "1"]
    if spec.model:
        cmd += ["-m", spec.model]
    if spec.provider:
        cmd += ["--provider", spec.provider]
    env = os.environ.copy()
    env.setdefault("HERMES_ACCEPT_HOOKS", "1")
    last_error = None
    for _ in range(2):
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=240, env=env)
        combined = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        if result.returncode != 0:
            last_error = RuntimeError(f"Hermes exited {result.returncode}: {combined[-2000:]}")
            continue
        try:
            return extract_json(combined)
        except Exception as exc:  # retry once; LLMs sometimes get cute.
            last_error = exc
    raise RuntimeError(str(last_error))


def validate_output(output: dict, choices: list[str]) -> dict:
    prediction = output.get("prediction")
    if prediction not in choices:
        raise ValueError(f"prediction {prediction!r} not in {choices!r}")
    scorers = output.get("goal_scorers")
    if isinstance(scorers, str):
        scorers = [s.strip() for s in scorers.split(",") if s.strip()]
    if not isinstance(scorers, list) or len(scorers) != 3:
        raise ValueError(f"goal_scorers must be a 3-item list, got {scorers!r}")
    confidence = float(output.get("confidence", 0))
    if not 0 <= confidence <= 1:
        raise ValueError(f"confidence out of range: {confidence}")
    return {
        "prediction": prediction,
        "scoreline": str(output.get("scoreline", "")).strip(),
        "goal_scorers": normalize_goal_scorers(", ".join(map(str, scorers))),
        "confidence": confidence,
        "rationale": str(output.get("rationale", "")).strip(),
        "news_summary": str(output.get("news_summary", "")).strip(),
    }


def main() -> int:
    args = build_parser().parse_args()
    specs = model_specs(args)
    matches = schedule_matches(args.days, args.tz, args.future_only)
    print(f"Resolved {len(matches)} match(es) for {args.days} local day(s) in {args.tz}:")
    for m in matches:
        print(f"  match_id={m['match_id']:>3} | {m['kickoff_local_human']} | {m['team1']} vs {m['team2']}")
    print("Models:", ", ".join(spec.alias for spec in specs))
    if args.dry_run:
        return 0

    store = load_store()
    existing = {
        (int(row.get("match_id")), row.get("model_alias"))
        for row in store.get("predictions", [])
        if row.get("match_id") is not None
    }
    saved = []
    skipped = []
    failures = []

    for m in matches:
        match_id = int(m["match_id"])
        prepared = None
        for spec in specs:
            if not args.force and (match_id, spec.alias) in existing:
                skipped.append({"match_id": match_id, "model_alias": spec.alias})
                print(f"SKIP match_id={match_id}: {spec.alias} already saved")
                continue
            try:
                print(f"\n=== match_id={match_id}: {m['team1']} vs {m['team2']} [{spec.alias}] ===", flush=True)
                if prepared is None:
                    prepared = prepare_match_data(match_id=match_id, news_results=args.news_results)
                raw = call_hermes(prompt_for(prepared, m["kickoff_local_human"]), spec)
                clean = validate_output(raw, prepared["choices"])
                record = {
                    "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "key": f"{normalize_match_key(prepared['match'])}::{spec.stored_model}",
                    "match_id": match_id,
                    "match": prepared["match"],
                    "choices": prepared["choices"],
                    "model_alias": spec.alias,
                    "model": spec.stored_model,
                    **clean,
                    "polymarket_odds": prepared["artifacts"].get("polymarket_odds", []),
                    "cache": {
                        "path": str(CACHE_PATH.relative_to(ROOT)),
                        "key": normalize_match_key(prepared["match"]),
                        "news_from_cache": prepared["cache"].get("news_from_cache"),
                        "polymarket_from_cache": prepared["cache"].get("polymarket_from_cache"),
                    },
                }
                store.setdefault("predictions", []).append(record)
                write_prediction_store(store)
                saved.append(record)
                print(f"SAVED {prepared['match']}: {record['prediction']} ({record['scoreline']}) confidence={record['confidence']}")
            except Exception as exc:
                failures.append({"match_id": match_id, "match": f"{m['team1']} vs {m['team2']}", "model_alias": spec.alias, "error": str(exc)})
                print(f"FAILED match_id={match_id} {spec.alias}: {exc}", file=sys.stderr, flush=True)

    print("\nSummary:")
    print(json.dumps({
        "saved": [{"match_id": r["match_id"], "match": r["match"], "model_alias": r["model_alias"], "prediction": r["prediction"], "scoreline": r["scoreline"], "confidence": r["confidence"]} for r in saved],
        "skipped": skipped,
        "failures": failures,
        "predictions_path": str(PREDICTIONS_PATH.relative_to(ROOT)),
    }, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
