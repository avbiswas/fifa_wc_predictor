from __future__ import annotations

import unittest

from worldcup_predictor.leverage_optimizer import (
    Odds,
    apply_exact_score_chase,
    apply_market_ev_backtest_guard,
    apply_selective_miracle_policy,
    apply_slate_draw_budget,
    choose_mode_from_state,
    comeback_draw_target,
    estimate_opponents_from_history,
    estimate_player_tendencies,
    known_predictions_for_match,
    optimize_match,
    parse_scoreline,
    project_opponent_pick,
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

    def test_group_stage_blocks_cute_draw_when_side_pick_is_better(self) -> None:
        row = optimize_match(
            match="Mexico vs Ecuador",
            odds=Odds(home=2.25, draw=3.0, away=3.8),
            over_under=1.5,
            field_predictions=[(2, 1), (3, 0), (3, 1), (2, 0)],
            leader_predictions=[(2, 1), (3, 0)],
            mode="controlled_attack",
            tournament_phase="group_stage",
        )
        self.assertEqual(row["ev_pick"]["scoreline"], "1:0")
        self.assertEqual(row["best_draw_pick"]["scoreline"], "0:0")
        self.assertEqual(row["final_pick"]["scoreline"], "1:0")

    def test_slate_draw_target_tracks_expected_draw_count_without_forcing_lunacy(self) -> None:
        self.assertEqual(slate_draw_target([0.25] * 8), 2)
        self.assertEqual(slate_draw_target([0.05] * 8), 0)
        self.assertLessEqual(slate_draw_target([0.35] * 8), 4)

    def test_apply_slate_draw_budget_promotes_best_draw_when_needed(self) -> None:
        rows = [
            {
                "match": "A-B",
                "fair_probabilities": {"draw": 0.30},
                "final_pick": {"scoreline": "2:1", "pick": "home", "expected_points": 1.25, "edge_vs_field": 0.2, "composite_score": 1.3},
                "best_draw_pick": {"scoreline": "1:1", "pick": "draw", "expected_points": 1.2, "edge_vs_field": 0.5, "p_gain_2plus": 0.3, "p_loss_2plus": 0.2, "composite_score": 1.25},
                "best_non_draw_pick": {"scoreline": "2:1", "pick": "home", "expected_points": 1.25, "composite_score": 1.3},
            },
            {
                "match": "C-D",
                "fair_probabilities": {"draw": 0.20},
                "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.7, "composite_score": 1.6},
                "best_draw_pick": {"scoreline": "1:1", "pick": "draw", "expected_points": 0.7, "edge_vs_field": 0.1, "p_gain_2plus": 0.1, "composite_score": 0.6},
                "best_non_draw_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.7, "composite_score": 1.6},
            },
        ]
        adjusted = apply_slate_draw_budget(rows, target_draws=1, tournament_phase="group_stage")
        self.assertEqual(sum(1 for row in adjusted if row["final_pick"]["pick"] == "draw"), 1)
        self.assertTrue(adjusted[0]["draw_budget_adjusted"])

    def test_group_stage_draw_budget_does_not_promote_downside_draw_quota(self) -> None:
        rows = [
            {
                "match": "Mexico-Ecuador",
                "fair_probabilities": {"draw": 0.32},
                "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.24, "edge_vs_field": 0.24, "composite_score": 1.2},
                "best_draw_pick": {
                    "scoreline": "0:0",
                    "pick": "draw",
                    "expected_points": 1.10,
                    "edge_vs_field": 0.10,
                    "p_gain_2plus": 0.36,
                    "p_loss_2plus": 0.42,
                    "composite_score": 1.36,
                },
                "best_non_draw_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.24, "composite_score": 1.2},
            }
        ]
        adjusted = apply_slate_draw_budget(rows, target_draws=1, tournament_phase="group_stage")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "1:0")
        self.assertFalse(adjusted[0].get("draw_budget_adjusted", False))

    def test_knockout_mode_hard_blocks_draw_final_picks(self) -> None:
        row = optimize_match(
            match="A vs B",
            odds=Odds(home=2.6, draw=2.8, away=2.6),
            over_under=1.5,
            field_predictions=[(1, 0), (2, 1), (0, 1), (1, 2)],
            leader_predictions=[(1, 0), (0, 1)],
            mode="desperation",
            tournament_phase="knockout",
        )
        self.assertNotEqual(row["final_pick"]["pick"], "draw")
        adjusted = apply_slate_draw_budget([row], target_draws=1, tournament_phase="knockout")
        self.assertEqual(adjusted[0]["final_pick"]["pick"], row["best_non_draw_pick"]["pick"])
        self.assertNotEqual(adjusted[0]["final_pick"]["pick"], "draw")

    def test_comeback_draw_target_caps_draw_traps_when_far_behind(self) -> None:
        auto_target = slate_draw_target([0.29] * 8)
        self.assertEqual(auto_target, 2)
        self.assertEqual(comeback_draw_target(auto_target, {"deficit": 10}, mode="controlled_attack"), 1)
        self.assertEqual(comeback_draw_target(auto_target, {"deficit": 3}, mode="controlled_attack"), 2)

    def test_selective_miracle_blocks_blind_upset_against_strong_favorite(self) -> None:
        row = {
            "status": "ok",
            "fair_probabilities": {"home": 0.74, "draw": 0.16, "away": 0.10},
            "final_pick": {
                "scoreline": "1:2",
                "pick": "away",
                "expected_points": 0.45,
                "p_gain_2plus": 0.10,
                "p_loss_2plus": 0.72,
                "leader_correlation": -0.4,
            },
            "ev_pick": {
                "scoreline": "2:0",
                "pick": "home",
                "expected_points": 1.90,
                "exact_probability": 0.18,
                "p_gain_2plus": 0.0,
                "p_loss_2plus": 0.0,
                "leader_correlation": 0.5,
            },
            "top_candidates": [
                {"scoreline": "1:2", "pick": "away", "expected_points": 0.45, "p_gain_2plus": 0.10, "p_loss_2plus": 0.72},
                {"scoreline": "2:0", "pick": "home", "expected_points": 1.90, "exact_probability": 0.18, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
                {"scoreline": "3:1", "pick": "home", "expected_points": 1.82, "exact_probability": 0.12, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
            ],
        }
        adjusted = apply_selective_miracle_policy([row], state={"deficit": 44}, mode="desperation")
        self.assertEqual(adjusted[0]["final_pick"]["pick"], "home")
        self.assertTrue(adjusted[0]["selective_miracle_adjusted"])
        self.assertIn("strong favorite protected", adjusted[0]["selection_reason"])

    def test_selective_miracle_allows_credible_balanced_market_swing(self) -> None:
        row = {
            "status": "ok",
            "fair_probabilities": {"home": 0.28, "draw": 0.29, "away": 0.43},
            "final_pick": {
                "scoreline": "2:1",
                "pick": "home",
                "expected_points": 0.76,
                "p_gain_2plus": 0.28,
                "p_loss_2plus": 0.43,
                "leader_correlation": -0.5,
            },
            "ev_pick": {"scoreline": "0:1", "pick": "away", "expected_points": 1.20, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
            "top_candidates": [
                {"scoreline": "2:1", "pick": "home", "expected_points": 0.76, "p_gain_2plus": 0.28, "p_loss_2plus": 0.43},
                {"scoreline": "0:1", "pick": "away", "expected_points": 1.20, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
            ],
        }
        adjusted = apply_selective_miracle_policy([row], state={"deficit": 44}, mode="desperation")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "2:1")
        self.assertTrue(adjusted[0]["selective_miracle_allowed"])
        self.assertEqual(adjusted[0]["tactical_posture"], "selective_swing")

    def test_exact_score_chase_upgrades_low_upside_same_side_pick(self) -> None:
        row = {
            "status": "ok",
            "match": "Favorite vs Dog",
            "fair_probabilities": {"home": 0.66, "draw": 0.20, "away": 0.14},
            "final_pick": {
                "scoreline": "1:0",
                "pick": "home",
                "expected_points": 1.55,
                "p_gain_2plus": 0.0,
                "p_loss_2plus": 0.0,
                "leader_correlation": 0.8,
            },
            "ev_pick": {
                "scoreline": "2:0",
                "pick": "home",
                "expected_points": 1.50,
                "p_gain_2plus": 0.08,
                "p_loss_2plus": 0.0,
                "leader_correlation": 0.7,
            },
            "top_candidates": [
                {
                    "scoreline": "1:0",
                    "pick": "home",
                    "expected_points": 1.55,
                    "p_gain_2plus": 0.0,
                    "p_loss_2plus": 0.0,
                    "leader_correlation": 0.8,
                },
                {
                    "scoreline": "2:0",
                    "pick": "home",
                    "expected_points": 1.50,
                    "p_gain_2plus": 0.08,
                    "p_loss_2plus": 0.0,
                    "leader_correlation": 0.7,
                },
            ],
        }
        adjusted = apply_exact_score_chase([row], state={"deficit": 10}, mode="controlled_attack")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "2:0")
        self.assertTrue(adjusted[0]["exact_chase_adjusted"])

    def test_exact_score_chase_stays_off_when_deficit_is_small(self) -> None:
        row = {
            "status": "ok",
            "fair_probabilities": {"home": 0.66, "draw": 0.20, "away": 0.14},
            "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.55},
            "top_candidates": [{"scoreline": "2:0", "pick": "home", "expected_points": 1.50}],
        }
        adjusted = apply_exact_score_chase([row], state={"deficit": 2}, mode="controlled_attack")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "1:0")

    def test_market_ev_guard_reverts_costly_comeback_leverage(self) -> None:
        row = {
            "status": "ok",
            "final_pick": {"scoreline": "3:1", "pick": "home", "expected_points": 1.42},
            "ev_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.55},
        }
        adjusted = apply_market_ev_backtest_guard([row], state={"deficit": 44}, mode="desperation")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "1:0")
        self.assertTrue(adjusted[0]["market_ev_guard_adjusted"])
        self.assertIn("backtest guard", adjusted[0]["selection_reason"])

    def test_market_ev_guard_keeps_near_free_leverage(self) -> None:
        row = {
            "status": "ok",
            "final_pick": {"scoreline": "2:1", "pick": "home", "expected_points": 1.52},
            "ev_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.55},
        }
        adjusted = apply_market_ev_backtest_guard([row], state={"deficit": 44}, mode="desperation")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "2:1")
        self.assertFalse(adjusted[0].get("market_ev_guard_adjusted", False))

    def test_market_ev_guard_keeps_credible_balanced_knockout_swing(self) -> None:
        row = {
            "status": "ok",
            "fair_probabilities": {"home": 0.275, "draw": 0.312, "away": 0.413},
            "final_pick": {
                "scoreline": "2:1",
                "pick": "home",
                "expected_points": 0.78,
                "p_gain_2plus": 0.274,
                "p_loss_2plus": 0.419,
            },
            "ev_pick": {"scoreline": "0:1", "pick": "away", "expected_points": 1.16},
        }
        adjusted = apply_market_ev_backtest_guard([row], state={"deficit": 44}, mode="desperation")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "2:1")
        self.assertEqual(adjusted[0]["market_ev_guard_skipped"], "credible balanced-market swing")

    def test_group_stage_exact_chase_does_not_inflate_balanced_low_total_games(self) -> None:
        row = {
            "status": "ok",
            "fair_probabilities": {"home": 0.43, "draw": 0.32, "away": 0.25},
            "over_under": 1.5,
            "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.24, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
            "top_candidates": [
                {"scoreline": "1:0", "pick": "home", "expected_points": 1.24, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
                {"scoreline": "2:1", "pick": "home", "expected_points": 1.14, "p_gain_2plus": 0.0, "p_loss_2plus": 0.0},
            ],
        }
        adjusted = apply_exact_score_chase([row], state={"deficit": 28}, mode="controlled_attack", tournament_phase="group_stage")
        self.assertEqual(adjusted[0]["final_pick"]["scoreline"], "1:0")

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

    def test_project_opponent_pick_reflects_scoring_style_and_favorite(self) -> None:
        favorite_match = Odds(home=1.8, draw=3.4, away=4.2)
        chaos_history = [(4, 2), (3, 1), (5, 2), (3, 2), (4, 1), (2, 2)]
        tight_history = [(1, 0), (2, 1), (1, 0), (2, 0), (2, 1), (1, 0)]
        chaos_pick = project_opponent_pick(chaos_history, favorite_match)
        tight_pick = project_opponent_pick(tight_history, favorite_match)
        # Both back the home favorite, but the high-scoring player projects more goals.
        self.assertGreater(chaos_pick[0], chaos_pick[1])
        self.assertGreater(tight_pick[0], tight_pick[1])
        self.assertGreater(sum(chaos_pick), sum(tight_pick))

    def test_project_opponent_pick_follows_the_market_favorite_side(self) -> None:
        home_history = [(2, 1), (2, 0), (1, 0), (3, 1)]
        away_favorite = Odds(home=4.2, draw=3.4, away=1.8)
        pick = project_opponent_pick(home_history, away_favorite)
        # Away is favored, so even a home-leaning player is projected onto an away win.
        self.assertLess(pick[0], pick[1])

    def test_estimate_opponents_from_history_excludes_niko_and_splits_leaders(self) -> None:
        context = {
            "current_state": {"niko_player": "Me"},
            "leader_names": ["Boss"],
            "round_history": (
                [{"player": "Me", "tip": "1:1"} for _ in range(6)]
                + [{"player": "Boss", "tip": "2:1", "is_leader": True} for _ in range(6)]
                + [{"player": "Rando", "tip": "2:0"} for _ in range(6)]
            ),
        }
        field, leaders = estimate_opponents_from_history(context, Odds(home=1.8, draw=3.4, away=4.2))
        self.assertEqual(len(field), 2)  # Boss + Rando, never Me
        self.assertEqual(len(leaders), 1)  # only Boss

    def test_estimate_opponents_from_history_empty_without_history(self) -> None:
        field, leaders = estimate_opponents_from_history({}, Odds(home=1.8, draw=3.4, away=4.2))
        self.assertEqual(field, [])
        self.assertEqual(leaders, [])

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
