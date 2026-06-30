from __future__ import annotations

import unittest

from worldcup_predictor.data import is_knockout_match, prediction_choices


class PredictionChoicesTests(unittest.TestCase):
    def test_group_stage_allows_draw(self) -> None:
        match = {"round": "Matchday 1", "team1": "Mexico", "team2": "South Africa"}
        self.assertFalse(is_knockout_match(match))
        self.assertEqual(prediction_choices(match), ["Mexico", "South Africa", "Draw"])

    def test_knockout_requires_winner(self) -> None:
        match = {"round": "Round of 32", "team1": "Brazil", "team2": "Japan"}
        self.assertTrue(is_knockout_match(match))
        self.assertEqual(prediction_choices(match), ["Brazil", "Japan"])
