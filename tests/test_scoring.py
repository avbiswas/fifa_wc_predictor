from __future__ import annotations

import unittest

from worldcup_predictor.goal_scorers import normalize_goal_scorers
from worldcup_predictor.predictions import model_performance_context
from worldcup_predictor.results import _team_key
from worldcup_predictor.scoring import (
    score_goal_scorers,
    score_goal_difference,
    score_prediction,
    score_scoreline,
    scorer_names_match,
    update_leaderboard,
)


class GoalScorerNormalizationTests(unittest.TestCase):
    def test_limits_scorers_and_preserves_commas_inside_parentheses(self) -> None:
        value = (
            "Raul Jimenez (Mexico, FW), Guillermo Ochoa (Mexico, GK), "
            "Santiago Gimenez (Mexico, FW), Edson Alvarez (Mexico)"
        )
        self.assertEqual(
            normalize_goal_scorers(value),
            [
                "Raul Jimenez (Mexico, FW)",
                "Guillermo Ochoa (Mexico, GK)",
                "Santiago Gimenez (Mexico, FW)",
            ],
        )

    def test_removes_team_prefix(self) -> None:
        self.assertEqual(
            normalize_goal_scorers("Mexico: Raul Jimenez, Edson Alvarez, Orbelin Pineda, South Africa: Lyle Foster"),
            ["Raul Jimenez", "Edson Alvarez", "Orbelin Pineda"],
        )


class ScoringTests(unittest.TestCase):
    def test_scoreline_tiers(self) -> None:
        self.assertEqual(score_scoreline((2, 1), (2, 1)), 25)
        self.assertEqual(score_scoreline((3, 2), (2, 1)), 0)
        self.assertEqual(score_scoreline((1, 2), (2, 1)), 0)
        self.assertEqual(score_scoreline((0, 0), (2, 1)), 0)

    def test_goal_difference_is_scored_separately(self) -> None:
        self.assertEqual(score_goal_difference((2, 1), (2, 1)), 10)
        self.assertEqual(score_goal_difference((3, 2), (2, 1)), 10)
        self.assertEqual(score_goal_difference((1, 2), (2, 1)), 0)

    def test_goal_scorers_match_abbreviated_and_korean_names(self) -> None:
        self.assertTrue(scorer_names_match("Raúl Jiménez (Mexico)", "R. Jiménez"))
        self.assertTrue(scorer_names_match("Hwang In-beom (South Korea)", "I.B. Hwang"))
        self.assertFalse(scorer_names_match("Hwang Hee-chan", "I.B. Hwang"))
        points, breakdown = score_goal_scorers(
            ["Raúl Jiménez", "Julián Quiñones", "Edson Álvarez"],
            [{"scorer": "R. Jiménez"}, {"scorer": "J. Quiñones"}],
        )
        self.assertEqual(points, 10)
        self.assertEqual([row["points"] for row in breakdown], [5, 5, 0])

    def test_perfect_prediction_is_capped_at_100(self) -> None:
        prediction = {
            "prediction": "Mexico",
            "scoreline": "Mexico 2-1 South Africa",
            "goal_scorers": ["Raul Jimenez", "Julian Quinones", "Santiago Gimenez"],
        }
        result = {
            "winner": "Mexico",
            "team1_score": 2,
            "team2_score": 1,
            "goals": [
                {"scorer": "R. Jimenez"},
                {"scorer": "J. Quinones"},
                {"scorer": "S. Gimenez"},
            ],
        }
        score = score_prediction(prediction, result)
        self.assertEqual(score["total"], 100)
        self.assertEqual(score["result"], 50)
        self.assertEqual(score["scoreline"], 25)
        self.assertEqual(score["goal_difference"], 10)
        self.assertEqual(score["goal_scorers"], 15)

    def test_leaderboard_uses_latest_prediction_per_model_and_match(self) -> None:
        store = {
            "results": {"1": {"match_id": 1}},
            "predictions": [
                {"match_id": 1, "model_alias": "gpt-5.5", "usage": {"totals": {"cost": 0.01}}, "score": {"total": 10, "result": 0, "scoreline": 0, "goal_difference": 10, "goal_scorers": 0}},
                {"match_id": 1, "model_alias": "gpt-5.5", "usage": {"totals": {"cost": 0.03}}, "score": {"total": 100, "result": 50, "scoreline": 25, "goal_difference": 10, "goal_scorers": 15}},
                {"match_id": 2, "model_alias": "gpt-5.5", "usage": {"totals": {"cost": 0.02}}},
            ],
        }
        leaderboard = update_leaderboard(
            store,
            [{"match_id": "1", "round": "Matchday 1"}],
        )
        gpt = next(row for row in leaderboard["rows"] if row["model_alias"] == "gpt-5.5")
        self.assertEqual(gpt["matches_scored"], 1)
        self.assertEqual(gpt["total_points"], 100)
        self.assertEqual(gpt["total_cost"], 0.05)
        self.assertEqual(leaderboard["completed_matchdays"], 1)
        self.assertTrue(leaderboard["available"])

    def test_leaderboard_accepts_external_model_aliases(self) -> None:
        store = {
            "results": {"1": {"match_id": 1}},
            "predictions": [
                {
                    "match_id": 1,
                    "model_alias": "hermes-gpt-5.5-codex",
                    "usage": {"totals": {"cost": 0}},
                    "score": {"total": 60, "result": 50, "scoreline": 0, "goal_difference": 10, "goal_scorers": 0},
                },
            ],
        }
        leaderboard = update_leaderboard(store, [{"match_id": "1", "round": "Matchday 1"}])
        hermes = next(row for row in leaderboard["rows"] if row["model_alias"] == "hermes-gpt-5.5-codex")
        self.assertEqual(hermes["matches_scored"], 1)
        self.assertEqual(hermes["total_points"], 60)


class ModelPerformanceContextTests(unittest.TestCase):
    def test_formats_latest_five_scored_predictions_for_same_model(self) -> None:
        store = {
            "results": {
                str(index): {
                    "team1": f"Team {index}A",
                    "team2": f"Team {index}B",
                    "team1_score": index % 3,
                    "team2_score": (index + 1) % 3,
                    "winner": "Draw" if index == 2 else f"Team {index}A",
                }
                for index in range(1, 8)
            },
            "predictions": [
                {
                    "created_at": f"2026-06-{index:02d}T00:00:00Z",
                    "match_id": index,
                    "match": f"Team {index}A vs Team {index}B",
                    "model_alias": "gemini-3.5-flash",
                    "model": "openrouter/google/gemini-3.5-flash",
                    "scoreline": f"Team {index}A 2-1 Team {index}B",
                    "score": {"total": index * 10},
                }
                for index in range(1, 8)
            ]
            + [
                {
                    "created_at": "2026-06-09T00:00:00Z",
                    "match_id": 9,
                    "match": "Other A vs Other B",
                    "model_alias": "other-model",
                    "model": "openrouter/other",
                    "scoreline": "Other A 1-0 Other B",
                    "score": {"total": 100},
                },
                {
                    "created_at": "2026-06-10T00:00:00Z",
                    "match_id": 10,
                    "match": "Unscored A vs Unscored B",
                    "model_alias": "gemini-3.5-flash",
                    "model": "openrouter/google/gemini-3.5-flash",
                    "scoreline": "Unscored A 1-0 Unscored B",
                },
            ],
        }

        context = model_performance_context(
            store,
            model_alias="gemini-3.5-flash",
            model="openrouter/google/gemini-3.5-flash",
            current_match_id=7,
        )

        lines = context.splitlines()
        self.assertEqual(lines[0], "Your last 5 match performances:")
        self.assertEqual(len(lines), 6)
        self.assertIn("1 | Team 6A vs Team 6B | You predicted Team 6A 2-1 Team 6B", lines[1])
        self.assertIn("Your points: 60/100", lines[1])
        self.assertNotIn("Team 7A", context)
        self.assertNotIn("Other A", context)
        self.assertNotIn("Unscored A", context)

    def test_returns_empty_history_message_when_model_has_no_scored_rows(self) -> None:
        self.assertEqual(
            model_performance_context({}, "gemini-3.5-flash", "openrouter/google/gemini-3.5-flash"),
            "Your last 5 match performances:\nNo scored match history available yet.",
        )


class ResultNormalizationTests(unittest.TestCase):
    def test_common_international_team_aliases(self) -> None:
        self.assertEqual(_team_key("Korea Republic"), _team_key("South Korea"))
        self.assertEqual(_team_key("Czechia"), _team_key("Czech Republic"))
        self.assertEqual(_team_key("Côte d'Ivoire"), _team_key("Ivory Coast"))
        self.assertEqual(_team_key("Congo DR"), _team_key("DR Congo"))


if __name__ == "__main__":
    unittest.main()
