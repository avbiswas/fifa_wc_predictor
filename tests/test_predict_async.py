from __future__ import annotations

import asyncio
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from worldcup_predictor.predict_async import _predict_one


class PredictAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_predict_one_accepts_knockout_choices_without_draw(self) -> None:
        prepared = {
            "match": "Ivory Coast vs Norway",
            "choices": ["Ivory Coast", "Norway"],
            "match_row": {"team1": "Ivory Coast", "team2": "Norway"},
            "model_inputs": {
                "match": "Ivory Coast vs Norway",
                "match_context": "{}",
                "team1_squad": "",
                "team2_squad": "",
                "recent_record": "",
                "polymarket_odds": "[]",
            },
            "artifacts": {"polymarket_odds": []},
        }

        class DummyPredictor:
            def __init__(self, team1: str, team2: str, allow_draw: bool = True):
                self.team1 = team1
                self.team2 = team2
                self.allow_draw = allow_draw

            async def acall(self, **_: str):
                return SimpleNamespace(
                    prediction="Ivory Coast",
                    scoreline="Ivory Coast 1-1 Norway",
                    goal_scorers="Player One, Player Two, Player Three",
                    confidence=0.55,
                    rationale="Knockout tie decided on penalties.",
                )

        with (
            patch("worldcup_predictor.predict_async.resolve_model", return_value=("alias", "resolved")),
            patch("worldcup_predictor.predict_async.make_lm", return_value=object()),
            patch("worldcup_predictor.predict_async.MatchPredictor", DummyPredictor),
            patch("worldcup_predictor.predict_async.model_performance_context", return_value=""),
            patch("worldcup_predictor.predict_async.extract_lm_usage", return_value={}),
            patch("worldcup_predictor.predict_async.dspy.settings", SimpleNamespace(context=lambda **_: nullcontext())),
        ):
            output = await _predict_one("alias", 78, prepared, "", {}, asyncio.Semaphore(1))

        self.assertEqual(output["choices"], ["Ivory Coast", "Norway"])
        self.assertEqual(output["prediction"], "Ivory Coast")
        self.assertEqual(output["scoreline"], "Ivory Coast 1-1 Norway")
