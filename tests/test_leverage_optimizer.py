from __future__ import annotations

import unittest

from worldcup_predictor.leverage_optimizer import (
    Odds,
    apply_slate_draw_budget,
    choose_mode_from_state,
    estimate_player_tendencies,
    known_predictions_for_match,
    optimize_match,
    parse_scoreline,
    rank_leverage_candidates,
    slate_draw_target,
)


class LeverageOptimizerTests(unittest.TestCase):
    def test_parse_scoreline_accepts_colon_and_dash(self) -> None:
        self.assertEqual(parse_scoreline("2:1"), (2, 1))
        self.assertEqual(parse_scoreline("2-1"), (2, 1))

    def test_draw_pick_has_gain_against_favorite_chalk_when_draw_lands(self) -> None:
        distribution = {(1, 1): 0.35, (2, 1): 0.30, (1, 0): 0.20, (0, 1): 0.15}
        ranked = rank_leverage_candidates(distribution, field_predictions=[(2, 1), (2, 0), (1, 0)], leader_predictions=[(2, 1)])
        draw = next(candidate for candidate in ranked if candidate.scoreline == "1:1")
        self.assertGreaterEqual(draw.p_gain_2plus, 0.35)
        self.assertGreater(draw.p_loss_2plus, 0.0)

    def test_controlled_attack_does_not_force_draw_when_ev_cost_is_too_high(self) -> None:
        row = optimize_match(
            match="A vs B",
            odds=Odds(home=2.25, draw=3.25, away=3.35),
            field_predictions=[(2, 1), (2, 0), (1, 0)],
            leader_predictions=[(2, 1)],
            mode="controlled_attack",
        )
        self.assertEqual(row["final_pick"]["scoreline"], "1:0")
        self.assertEqual(row["best_draw_pick"]["scoreline"], "1:1")

    def test_slate_draw_target_tracks_expected_draw_count_without_forcing_lunacy(self) -> None:
        self.assertEqual(slate_draw_target([0.25] * 8), 2)
        self.assertEqual(slate_draw_target([0.05] * 8), 0)
        self.assertLessEqual(slate_draw_target([0.35] * 8), 4)

    def test_apply_slate_draw_budget_promotes_best_draw_when_needed(self) -> None:
        rows = [
            {
                "match": "A-B",
                "fair_probabilities": {"draw": 0.30},
                "final_pick": {"scoreline": "2:1", "pick": "home", "expected_points": 1.4, "composite_score": 1.3},
                "best_draw_pick": {"scoreline": "1:1", "pick": "draw", "expected_points": 1.2, "edge_vs_field": 0.5, "p_gain_2plus": 0.3, "composite_score": 1.25},
                "best_non_draw_pick": {"scoreline": "2:1", "pick": "home", "expected_points": 1.4, "composite_score": 1.3},
            },
            {
                "match": "C-D",
                "fair_probabilities": {"draw": 0.20},
                "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.7, "composite_score": 1.6},
                "best_draw_pick": {"scoreline": "1:1", "pick": "draw", "expected_points": 0.7, "edge_vs_field": 0.1, "p_gain_2plus": 0.1, "composite_score": 0.6},
                "best_non_draw_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.7, "composite_score": 1.6},
            },
        ]
        adjusted = apply_slate_draw_budget(rows, target_draws=1)
        self.assertEqual(sum(1 for row in adjusted if row["final_pick"]["pick"] == "draw"), 1)
        self.assertTrue(adjusted[0]["draw_budget_adjusted"])

    def test_mode_from_state(self) -> None:
        self.assertEqual(choose_mode_from_state({"deficit": 6, "remaining_matches": 20}), "controlled_attack")
        self.assertEqual(choose_mode_from_state({"deficit": 7, "remaining_matches": 3}), "desperation")
        self.assertEqual(choose_mode_from_state({"spieltag_lead": 2, "remaining_matches": 2}), "protect_spieltag_win")

    def test_known_predictions_for_match(self) -> None:
        context = {
            "leader_names": ["Leader"],
            "known_picks": [
                {"event_id": "1", "player": "Leader", "tip": "2:1"},
                {"event_id": "1", "player": "Friend", "tip": "1:1"},
            ],
        }
        field, leaders = known_predictions_for_match(context, event_id="1")
        self.assertEqual(field, [(2, 1), (1, 1)])
        self.assertEqual(leaders, [(2, 1)])

    def test_known_predictions_match_only_rows_do_not_bleed_across_event_ids(self) -> None:
        context = {
            "leader_names": ["Leader"],
            "known_picks": [
                {"match": "France vs Senegal", "player": "Leader", "tip": "2:1"},
                {"match": "Iraq vs Norway", "player": "Friend", "tip": "0:1"},
                {"player": "Unattached", "tip": "1:1"},
            ],
        }
        field, leaders = known_predictions_for_match(context, event_id="99", match="France vs Senegal")
        self.assertEqual(field, [(2, 1)])
        self.assertEqual(leaders, [(2, 1)])

    def test_estimate_player_tendencies(self) -> None:
        tendencies = estimate_player_tendencies(
            [
                {"player": "Chaos", "tip": "4:3", "favorite": "home"},
                {"player": "Chaos", "tip": "1:1", "favorite": "home"},
                {"player": "Sharp", "tip": "1:1", "favorite": "draw"},
            ]
        )
        chaos = next(row for row in tendencies if row.player == "Chaos")
        self.assertGreater(chaos.chaos_rate, 0.0)
        sharp = next(row for row in tendencies if row.player == "Sharp")
        self.assertEqual(sharp.draw_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
