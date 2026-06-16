from __future__ import annotations

import unittest

from worldcup_predictor.tip_optimizer import (
    DIXON_COLES_RHO,
    Odds,
    ScoreRules,
    american_to_decimal,
    dixon_coles_tau,
    draw_guard_tip,
    exploit_engine_tip,
    fair_probabilities,
    market_optimal_tip,
    poisson_distribution,
    score_tip,
    war_machine_tip,
)


class TipOptimizerTests(unittest.TestCase):
    def test_fair_probabilities_remove_bookmaker_margin(self) -> None:
        probs = fair_probabilities(Odds(2.0, 3.5, 3.7))
        self.assertAlmostEqual(sum(probs.values()), 1.0)
        self.assertGreater(probs["home"], probs["away"])

    def test_draw_guard_picks_draw_when_market_says_draw_is_live(self) -> None:
        tip = draw_guard_tip(Odds(2.0, 3.5, 3.7))
        self.assertEqual(tip.scoreline, "1:1")
        self.assertEqual(tip.pick, "draw")

    def test_draw_guard_keeps_mega_favorite(self) -> None:
        tip = draw_guard_tip(Odds(1.05, 17.0, 51.0))
        self.assertEqual(tip.scoreline, "3:0")
        self.assertEqual(tip.pick, "home")

    def test_american_odds_conversion(self) -> None:
        self.assertAlmostEqual(american_to_decimal("+600"), 7.0)
        self.assertAlmostEqual(american_to_decimal("-215"), 1.465116279, places=6)

    def test_market_optimal_tip_returns_plausible_score(self) -> None:
        tip = market_optimal_tip(Odds(1.465, 4.6, 7.0), over_under=2.5)
        self.assertEqual(tip.pick, "home")
        self.assertIn(tip.scoreline, {"1:0", "2:0", "2:1", "3:0"})

    def test_exploit_engine_does_not_donate_ev_to_draw_trap(self) -> None:
        # Draw is "live" here (fair draw ~29%, favorite ~43%), but 1:1 EV (~0.80) is far
        # below the EV-optimal 1:0 (~1.23). The engine must NOT throw away ~0.4 pts/match.
        tip = exploit_engine_tip(Odds(2.25, 3.3, 3.4))
        self.assertEqual(tip.scoreline, "1:0")
        self.assertEqual(tip.pick, "home")

    def test_exploit_engine_keeps_draw_only_on_a_near_tie(self) -> None:
        # With a generous EV slack, the same live-draw match breaks toward 1:1.
        tip = exploit_engine_tip(Odds(2.25, 3.3, 3.4), draw_ev_slack=0.5)
        self.assertEqual(tip.scoreline, "1:1")
        self.assertIn("draw tie-break", tip.reason)

    def test_exploit_engine_keeps_draw_when_market_ev_already_favors_it(self) -> None:
        # In a genuinely low-scoring, balanced game a draw scoreline (0:0) is EV-optimal,
        # so market_optimal_tip already returns it and the engine passes it through.
        tip = exploit_engine_tip(Odds(2.6, 2.8, 2.6), over_under=1.5)
        self.assertEqual(tip.pick, "draw")

    def test_war_machine_alias_remains_for_old_scripts(self) -> None:
        # Backward-compatible alias inherits the EV-respecting behavior.
        self.assertEqual(war_machine_tip(Odds(2.25, 3.3, 3.4)).scoreline, "1:0")

    def test_poisson_distribution_normalizes(self) -> None:
        for rho in (0.0, DIXON_COLES_RHO):
            distribution = poisson_distribution(1.4, 1.1, rho=rho)
            self.assertAlmostEqual(sum(distribution.values()), 1.0)
            self.assertGreaterEqual(min(distribution.values()), 0.0)

    def test_dixon_coles_rho_zero_recovers_independent_poisson(self) -> None:
        # With rho=0 the joint factorizes into the product of the Poisson marginals.
        distribution = poisson_distribution(1.6, 1.2, rho=0.0)
        p_home_1 = sum(p for (h, a), p in distribution.items() if h == 1)
        p_away_1 = sum(p for (h, a), p in distribution.items() if a == 1)
        self.assertAlmostEqual(distribution[(1, 1)], p_home_1 * p_away_1, places=4)

    def test_dixon_coles_lifts_draws_and_trims_single_goal_wins(self) -> None:
        independent = poisson_distribution(1.5, 1.2, rho=0.0)
        corrected = poisson_distribution(1.5, 1.2, rho=DIXON_COLES_RHO)
        self.assertGreater(corrected[(1, 1)], independent[(1, 1)])
        self.assertLess(corrected[(1, 0)], independent[(1, 0)])
        self.assertLess(corrected[(0, 1)], independent[(0, 1)])

    def test_dixon_coles_tau_only_touches_low_score_cells(self) -> None:
        self.assertEqual(dixon_coles_tau(2, 1, 1.5, 1.2, DIXON_COLES_RHO), 1.0)
        self.assertAlmostEqual(dixon_coles_tau(1, 1, 1.5, 1.2, DIXON_COLES_RHO), 1.0 - DIXON_COLES_RHO)

    def test_tip_scoring_default_round(self) -> None:
        rules = ScoreRules(exact=4, goal_difference=3, tendency=2)
        self.assertEqual(score_tip((1, 1), (1, 1), rules), 4)
        self.assertEqual(score_tip((1, 1), (2, 2), rules), 2)
        self.assertEqual(score_tip((3, 0), (7, 1), rules), 2)
        self.assertEqual(score_tip((2, 1), (1, 1), rules), 0)


if __name__ == "__main__":
    unittest.main()
