from __future__ import annotations

import unittest

from worldcup_predictor.ensemble import build_ensemble_report, build_model_weights, forecast_match


def scored_prediction(match_id: int, alias: str, pick: str, total: int, result_points: int = 50) -> dict:
    return {
        "match_id": match_id,
        "model_alias": alias,
        "prediction": pick,
        "scoreline": f"{pick} 1-0 Other",
        "confidence": 0.6,
        "created_at": f"2026-06-{match_id:02d}T00:00:00Z",
        "score": {"total": total, "result": result_points, "scoreline": 0, "goal_difference": 0, "goal_scorers": 0},
    }


class EnsembleTests(unittest.TestCase):
    def test_model_weights_ignore_low_coverage_leaderboard_confetti(self) -> None:
        store = {
            "results": {str(i): {"winner": "A"} for i in range(1, 5)},
            "predictions": [
                scored_prediction(1, "model-a", "A", 100),
                scored_prediction(2, "model-a", "A", 90),
                scored_prediction(3, "model-a", "A", 80),
                scored_prediction(4, "model-a", "A", 70),
                scored_prediction(1, "model-b", "A", 50),
                scored_prediction(2, "model-b", "A", 50),
                scored_prediction(3, "model-b", "A", 50),
                scored_prediction(4, "model-b", "A", 50),
                scored_prediction(1, "one-match-wonder", "A", 100),
            ],
        }
        weights = build_model_weights(store, {"top_models": 5, "min_coverage_ratio": 0.75})
        aliases = [row["model_alias"] for row in weights["models"]]
        self.assertEqual(aliases, ["model-a", "model-b"])
        self.assertEqual(weights["required_matches"], 3)
        self.assertEqual(weights["models"][0]["weight"], 1.0)
        self.assertGreater(weights["models"][1]["weight"], 0.25)

    def test_draw_calibration_switches_when_enough_weighted_models_pick_draw(self) -> None:
        predictions = [
            {"match_id": 10, "model_alias": "model-a", "prediction": "Draw", "confidence": 0.57, "scoreline": "A 1-1 B"},
            {"match_id": 10, "model_alias": "model-b", "prediction": "Draw", "confidence": 0.58, "scoreline": "A 1-1 B"},
            {"match_id": 10, "model_alias": "model-c", "prediction": "A", "confidence": 0.61, "scoreline": "A 2-1 B"},
        ]
        model_weights = {
            "models": [
                {"model_alias": "model-a", "weight": 0.3},
                {"model_alias": "model-b", "weight": 0.3},
                {"model_alias": "model-c", "weight": 1.0},
            ]
        }
        forecast = forecast_match(predictions, model_weights, {"draw_vote_threshold": 2, "draw_probability_floor": 0.2})
        self.assertEqual(forecast["calibrated_pick"], "Draw")
        self.assertIn("draw_calibration", forecast["risk_flags"])

    def test_raw_draw_minority_calibration_keeps_scoreline_and_confidence_consistent(self) -> None:
        predictions = [
            {"match_id": 11, "model_alias": "model-a", "prediction": "A", "confidence": 0.62, "scoreline": "A 2-0 B"},
            {"match_id": 11, "model_alias": "model-b", "prediction": "A", "confidence": 0.60, "scoreline": "A 2-1 B"},
            {"match_id": 11, "model_alias": "model-c", "prediction": "A", "confidence": 0.55, "scoreline": "A 1-0 B"},
            {"match_id": 11, "model_alias": "model-d", "prediction": "A", "confidence": 0.55, "scoreline": "A 1-0 B"},
            {"match_id": 11, "model_alias": "model-e", "prediction": "Draw", "confidence": 0.52, "scoreline": "A 1-1 B"},
            {"match_id": 11, "model_alias": "model-f", "prediction": "Draw", "confidence": 0.51, "scoreline": "A 0-0 B"},
            {"match_id": 11, "model_alias": "model-g", "prediction": "Draw", "confidence": 0.50, "scoreline": "A 1-1 B"},
        ]
        model_weights = {"models": [{"model_alias": "model-a", "weight": 1.0}, {"model_alias": "model-b", "weight": 1.0}]}
        forecast = forecast_match(predictions, model_weights, {"raw_draw_vote_threshold": 3, "raw_draw_share_floor": 0.2})
        self.assertEqual(forecast["weighted_consensus"], "A")
        self.assertEqual(forecast["calibrated_pick"], "Draw")
        self.assertIn("raw_draw_minority_calibration", forecast["risk_flags"])
        self.assertGreater(forecast["calibrated_confidence"], 0)
        self.assertIn("1-1", forecast["scoreline"])

    def test_ensemble_report_compares_raw_weighted_and_calibrated_backtest(self) -> None:
        store = {
            "results": {
                "1": {"winner": "A", "team1_score": 1, "team2_score": 0},
                "2": {"winner": "Draw", "team1_score": 1, "team2_score": 1},
            },
            "predictions": [
                scored_prediction(1, "model-a", "A", 100),
                scored_prediction(1, "model-b", "A", 50),
                scored_prediction(2, "model-a", "Draw", 100),
                scored_prediction(2, "model-b", "B", 0, result_points=0),
                {"match_id": 3, "model_alias": "model-a", "prediction": "A", "scoreline": "A 2-1 B", "confidence": 0.6},
            ],
        }
        schedule = [
            {"match_id": "1", "team1": "A", "team2": "B", "kickoff_utc": "2026-06-01T00:00:00Z"},
            {"match_id": "2", "team1": "A", "team2": "B", "kickoff_utc": "2026-06-02T00:00:00Z"},
            {"match_id": "3", "team1": "A", "team2": "B", "kickoff_utc": "2026-06-03T00:00:00Z"},
        ]
        report = build_ensemble_report(store, schedule, {"min_matches_for_weight": 1, "min_coverage_ratio": 0.5, "top_models": 2})
        self.assertEqual(report["backtest"]["matches"], 2)
        self.assertIn("weighted_consensus_correct", report["backtest"])
        self.assertEqual(len(report["forecasts"]), 1)
        self.assertEqual(report["forecasts"][0]["match_id"], 3)


if __name__ == "__main__":
    unittest.main()
