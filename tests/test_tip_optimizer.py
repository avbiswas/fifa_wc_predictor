from __future__ import annotations

import unittest

from worldcup_predictor.tip_optimizer import Odds, ScoreRules, american_to_decimal, draw_guard_tip, exploit_engine_tip, fair_probabilities, market_optimal_tip, score_tip, war_machine_tip


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

    def test_exploit_engine_overrides_live_draw_trap(self) -> None:
        tip = exploit_engine_tip(Odds(2.25, 3.3, 3.4))
        self.assertEqual(tip.scoreline, "1:1")
        self.assertIn("draw trap", tip.reason)

    def test_war_machine_alias_remains_for_old_scripts(self) -> None:
        self.assertEqual(war_machine_tip(Odds(2.25, 3.3, 3.4)).scoreline, "1:1")

    def test_tip_scoring_default_round(self) -> None:
        rules = ScoreRules(exact=4, goal_difference=3, tendency=2)
        self.assertEqual(score_tip((1, 1), (1, 1), rules), 4)
        self.assertEqual(score_tip((1, 1), (2, 2), rules), 2)
        self.assertEqual(score_tip((3, 0), (7, 1), rules), 2)
        self.assertEqual(score_tip((2, 1), (1, 1), rules), 0)


if __name__ == "__main__":
    unittest.main()
