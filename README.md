# KickTipp Exploit Engine

This repo is now built for one job: **beat Niko's friends in KickTipp**.

That means the engine optimizes the private contest, not generic football accuracy. A plausible scoreline that everyone else also picks is not enough. The system ranks exact-result tips by KickTipp expected value, draw coverage, leverage against friend-field chalk, leader correlation, and current table state.

The physical repo/package still uses some legacy `worldcup_predictor` names so older scripts keep working. Product direction is no longer “LLMs predict the World Cup.” The product is a **KickTipp exploit engine**.

## Core idea

KickTipp scoring observed in this round:

- exact result: 4
- correct tendency: 2
- winner + correct goal difference: 3
- non-exact draw: 2
- tips close 0 minutes before kickoff
- tiebreaker: matchday wins (`Spieltagsiege`)

The engine asks the right question:

> Which scoreline maximizes Niko's chance to win the private round?

Not:

> What is the most tasteful, obvious football prediction?

That second question is how you produce last-place sludge.

## What the engine uses

- ESPN public World Cup scoreboard and summary endpoints
- DraftKings-style moneyline odds exposed in ESPN summaries
- no-vig 1/X/2 probabilities
- Dixon-Coles-corrected Poisson scoreline distribution fitted to market probabilities and over/under (low-score correction lifts 0:0/1:1, the exact scores that actually land)
- KickTipp-specific expected-points scoring
- draw-trap tuning from completed matches
- friend/leader context from `data/kicktipp/rounds.json`
- slate-level draw budgeting
- bonus-question probability + ownership/leverage optimization
- optional Elo, news, roster, venue, and weather enrichment

## Main commands

```bash
cd /Users/niko/Projects/fifa_wc_predictor

# Install / verify environment
/Users/niko/.local/bin/uv sync

# The real entry sheet: EV + leverage + slate draw budget
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/generate_leverage_tip_sheet.py --days 3 --compact

# Full evidence report
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/generate_leverage_tip_sheet.py --days 3

# Baseline market/draw-trap sheet only; useful for debugging, not final entries
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/generate_tip_sheet.py --days 3 --compact

# Tune draw-trap thresholds from completed matches
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/tune_kicktipp_optimizer.py --days-back 14

# Backtest archived pre-kickoff picks once actual scorelines are available
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/backtest_kicktipp_optimizer.py --days-back 14

# Debug-only old behavior: recompute from current ESPN odds if no archive exists
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/backtest_kicktipp_optimizer.py --days-back 14 --fallback-live-recompute

# Optimize bonus-question answer sets after filling data/kicktipp/bonus_questions.json
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/optimize_bonus_questions.py

# Regression tests
PYTHONPATH=. /Users/niko/.local/bin/uv run --with pytest pytest -q
```

## Output files

Generated reports are ignored by git and written under `reports/`:

- `reports/leverage_tip_sheet.md` / `.json` — final private-league entry sheet
- `reports/tip_sheet.md` / `.json` — baseline market EV/draw-trap sheet
- `reports/kicktipp_optimizer_backtest.md` / `.json` — completed-match strategy backtest
- `reports/bonus_question_optimizer.md` / `.json` — bonus answer-set optimizer output
- `reports/tip_sheet_watchdog.md` / `.json` — cron/watchdog sheet

Append-only local archives are ignored by git and written under:

- `data/kicktipp/archive/reports/YYYY-MM-DD/*.json` — immutable full leverage-sheet snapshots
- `data/kicktipp/archive/picks.jsonl` — one pre-kickoff decision record per generated match/timestamp
- `data/kicktipp/archive/latest_by_event/*.json` — latest pre-kickoff pick per event for clean backtests

This archive is the important bit for serious evaluation. The report files are just the latest view; the archive is what lets us score exactly what we would have submitted after the result lands. The CLI sheet and cron/watchdog both write it.

Tracked config/context:

- `config/kicktipp_optimizer.json` — current tuned draw-trap thresholds
- `data/kicktipp/rounds.json` — Niko state, leaders, known friend picks, and round history
- `data/kicktipp/bonus_questions.json` — fill-in template for bonus pages

## Friend-field context

Fill `data/kicktipp/rounds.json` when screenshots or live friend picks are available:

```json
{
  "known_picks": [
    {
      "event_id": "401772000",
      "player": "Toegamorf",
      "tip": "2:1",
      "is_leader": true
    }
  ]
}
```

If no friend picks are known for the specific fixture, the engine now projects each tracked opponent from their real `round_history` (revealed draw/scoring/contrarian tendencies rotated onto the match), and only falls back to a generic public-chalk template when there is no history. Each row reports its `field_source` (`known_picks` / `history_projection` / `generic_template`). Real friend data is better. Screenshots beat vibes.

## Bonus questions

Fill `data/kicktipp/bonus_questions.json` with real options:

```json
{
  "questions": [
    {
      "id": "group_winners",
      "question": "Pick group winners",
      "slots": 12,
      "points": 4,
      "contrarian_slots": 2,
      "options": [
        {
          "label": "Brazil",
          "probability": 0.62,
          "ownership": 0.80,
          "category": "Group C"
        }
      ]
    }
  ]
}
```

The optimizer mostly takes the best probabilities, then reserves lower-owned upside slots when the tournament mode calls for catch-up leverage.

## Tournament modes

`generate_leverage_tip_sheet.py` chooses from `data/kicktipp/rounds.json`, or you can override:

```bash
PYTHONPATH=. /Users/niko/.local/bin/uv run python scripts/generate_leverage_tip_sheet.py --mode desperation --days 3
```

Modes:

- `safe` — protect lead, avoid 2+ point losses
- `balanced` — EV first, modest leverage
- `controlled_attack` — current default while trailing but not panicking
- `desperation` — late catch-up mode
- `protect_spieltag_win` — preserve matchday-win tiebreaker chances

## Legacy LLM prediction stack

The old LLM/model-roster workflow still exists for experiments and historical reports:

- `scripts/run_hermes_predictions.py`
- `scripts/run_model_roster.py`
- `scripts/backtest_predictions.py`
- `scripts/ensemble_forecast.py`
- `data/predictions/predictions.json`
- `cloudflare_app/public/data/predictions.json`

Treat that as supporting infrastructure. The final KickTipp pick should come from `generate_leverage_tip_sheet.py`, not from a raw LLM scoreline.

## Docs

See:

```text
docs/kicktipp_exploit_engine.md
```
