# LLMs predict FIFA World Cup 2026!

LLMs predict matchday scores, and get points for correct predictions.
This webapp is hosted [here](https://fifa-wc-predictor.sudavivi.workers.dev/)

https://github.com/user-attachments/assets/f19e6deb-2467-43e4-96d7-b831e6116b89



## Support

If you find this helpful, consider supporting on Patreon — it hosts all code, projects, slides, and write-ups from the YouTube channel.

[<img src="https://c5.patreon.com/external/logo/become_a_patron_button.png" alt="Become a Patron!" width="200">](https://www.patreon.com/NeuralBreakdownwithAVB)

## Data

Run:

```bash
uv run python scripts/download_worldcup_data.py
```

The script writes raw source files to `data/raw/` and normalized tables to `data/processed/`.

Processed outputs:

- `schedule_2026.csv` / `.json`: all 104 fixtures with UTC kickoff timestamps.
- `teams_2026.csv` / `.json`: qualified teams, groups, roster sizes, and coaches.
- `players_2026.csv` / `.json`: official squad players with position, DOB, club, height, caps, and goals.
- `coaches_2026.csv`: coach rows extracted from the official FIFA squad list.
- `grounds_2026.csv`: match counts by host ground/city label.
- `sources.csv` / `.json`: source URLs, local paths, checksums, and file sizes.

Raw outputs include the official FIFA schedule PDF, official FIFA squad list PDF, openfootball's structured 2026 schedule, and historical World Cup match JSON files from 1930 through 2022.

## Notes

The official FIFA squad PDF does not preserve every name column boundary during text extraction. `players_2026.csv` therefore keeps `name_block`, the raw extracted player-name columns before DOB, alongside the parsed fields that are reliable for modeling.

## Quick DSPy Prediction

Set keys in `.env` or `.envrc`:

```bash
export EXA_API_KEY=...
export OPENROUTER_API_KEY=...
```

Run a one-match ChainOfThought prediction:

```bash
python3 scripts/predict_match_dspy.py "Mexico vs South Africa" --news-results 5
```

The prototype uses `openrouter/google/gemini-3.5-flash`, searches Exa for match news, summarizes the news with DSPy, tries Polymarket's public Gamma API for odds, and predicts exactly one of the two team names or `Draw`.

News and Polymarket responses are cached by normalized match string in `data/cache/match_retrieval_cache.json`, so repeated runs for the same match do not call those APIs again. Use `--refresh-cache` to force a new retrieval.

Prediction code is split into modules under `worldcup_predictor/`:

- `cli.py`: command orchestration.
- `data.py`: schedule lookup and squad summaries.
- `cache.py`: local news/Polymarket cache.
- `news.py`: Exa retrieval and formatting.
- `polymarket.py`: Polymarket market search.
- `prepare.py`: artifact assembly for a single match.
- `dspy_program.py`: DSPy signatures and model configuration.

Polymarket lookup tries the global Gamma search endpoint first and then the Polymarket US public gateway (`/v1/search`) as a fallback.

Prepare all non-DSPy artifacts for one match ID:

```bash
./prepare_data 1
```

This writes `data/prepared/match_1.json` with schedule context, squad summaries, formatted news, Polymarket odds, cache metadata, and the exact model input fields needed by the predictor.

Pretty-print downloaded data with Rich:

```bash
./show_data --match-id 1 --prepared --cache
```

Use `--all-players` for full squads or `--squad-limit 12` to change the compact display.

Run a prediction with an explicit model:

```bash
python3 scripts/predict_match_dspy.py --match-id 1 --model gemini-3.5-flash
```

List configured competition aliases:

```bash
python3 scripts/predict_match_dspy.py --list-models
```

Validate configured aliases against OpenRouter's model list:

```bash
python3 scripts/predict_match_dspy.py --validate-models
```

Run every competition model for a match:

```bash
./run_competition --match-id 1
```

Run only models missing a saved prediction:

```bash
./run_missing_predictions --match-id 1
```

Each prediction is appended to `data/predictions/predictions.json` with the model name, winner prediction, scoreline, three predicted goal scorers, confidence, reasoning, and LM usage. Add `--no-save` to print without writing prediction history.

## Results and scoring

Fetch a completed match result and score all saved predictions for it:

```bash
./fetch_result --match-id 1
```

If automatic fixture matching is ambiguous, pass the TheSportsDB event ID:

```bash
./fetch_result --match-id 1 --fixture-id 123456
```

Results, available goal scorers, and prediction scores are written to `data/predictions/predictions.json`. Final scores come from TheSportsDB's free public API; no result API key or paid plan is required. Recompute scores from already saved results without making API calls:

```bash
./score_predictions
```

Each match is worth 100 points: 50 for the correct 90-minute result, 25 for the exact scoreline, 10 for the correct goal difference, and 15 for predicted goal scorers.

Generate a local backtest report from saved predictions and fetched results:

```bash
PYTHONPATH=. uv run python scripts/backtest_predictions.py
```

This writes `reports/backtest_latest.json` and `reports/backtest_latest.md` with completed match scores, model summaries, per-prediction rows, and consensus results. Reports are generated artifacts and are ignored by git.

## Optional Hermes backend

If you use [Hermes Agent](https://github.com/NousResearch/hermes-agent), you can run prepared match artifacts through your locally configured Hermes model/provider without using the OpenRouter/DSPy path:

```bash
PYTHONPATH=. uv run python scripts/run_hermes_predictions.py --days 3
```

Run a mini-tournament across explicit Hermes providers/models:

```bash
PYTHONPATH=. uv run python scripts/run_hermes_predictions.py \
  --days 3 \
  --hermes-model gpt-5.5 --hermes-provider openai-codex \
  --hermes-model claude-sonnet-4.7 --hermes-provider anthropic
```

The script stores outputs in the same `data/predictions/predictions.json` schema using model aliases like `hermes-default`, `hermes-gpt-5.5-codex`, or `hermes-anthropic-claude-sonnet-4.7`.

Resolve the current day manually:

```bash
uv run ./resolve_day
```

The command first prints every match it intends to predict and every result it intends to fetch. It then asks once whether to fetch all pending past results, followed by a separate approval prompt for each future match prediction batch. Enter `y` or `Y` to approve an action.

This command:

- runs only missing model predictions for resolved fixtures kicking off within the next 24 hours;
- fetches only missing results for matches whose kickoff time has passed;
- recalculates scores and the model leaderboard;
- records a one-hour retry window when a result is not final yet.

It is idempotent: predictions and completed results already present in the JSON are not requested again. Use `uv run ./resolve_day --dry-run` to print the plan and exit without prompting.

For an offline wiring check:

```bash
python3 scripts/predict_match_dspy.py --match-id 1 --skip-news --skip-polymarket
```
