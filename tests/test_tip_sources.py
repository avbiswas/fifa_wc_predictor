from __future__ import annotations

from datetime import datetime, timezone
import unittest

from worldcup_predictor.tip_sources import date_range, form_points, kicktipp_actual_score, normalize_team_name, parse_espn_odds


class TipSourcesTests(unittest.TestCase):
    def test_date_range(self) -> None:
        self.assertEqual(date_range(datetime(2026, 6, 16, tzinfo=timezone.utc), 3), "20260616-20260618")

    def test_parse_espn_odds(self) -> None:
        market = parse_espn_odds(
            {
                "odds": [
                    {
                        "provider": {"name": "DraftKings"},
                        "overUnder": 2.5,
                        "spread": -1.5,
                        "homeTeamOdds": {"moneyLine": -215},
                        "drawOdds": {"moneyLine": 360},
                        "awayTeamOdds": {"moneyLine": 600},
                    }
                ]
            }
        )
        assert market is not None
        self.assertEqual(market.provider, "DraftKings")
        self.assertAlmostEqual(market.odds.home, 1.465116279, places=6)
        self.assertEqual(market.odds.draw, 4.6)
        self.assertEqual(market.odds.away, 7.0)

    def test_normalize_team_aliases(self) -> None:
        self.assertEqual(normalize_team_name("Bosnia-Herzegovina"), normalize_team_name("Bosnia and Herzegovina"))
        self.assertEqual(normalize_team_name("Czechia"), normalize_team_name("Czech Republic"))
        self.assertEqual(normalize_team_name("Curaçao"), normalize_team_name("Curacao"))

    def test_form_points(self) -> None:
        self.assertEqual(form_points(["2026-01-01 Foo 1-0 W", "2026-01-02 Bar 1-1 D", "2026-01-03 Baz 0-2 L"]), 4)

    def test_kicktipp_actual_score_adds_penalty_shootout_goals(self) -> None:
        event = {
            "competitions": [
                {
                    "status": {"type": {"name": "STATUS_FINAL_PEN", "description": "Final Score - After Penalties"}},
                    "competitors": [
                        {"homeAway": "home", "score": "0", "shootoutScore": 4.0, "winner": True},
                        {"homeAway": "away", "score": "0", "shootoutScore": 3.0, "winner": False},
                    ],
                }
            ]
        }
        self.assertEqual(kicktipp_actual_score(event), (4, 3))

    def test_kicktipp_actual_score_preserves_penalty_winner_without_shootout_detail(self) -> None:
        event = {
            "competitions": [
                {
                    "status": {"type": {"name": "STATUS_FINAL_PEN"}},
                    "competitors": [
                        {"homeAway": "home", "score": "1", "winner": False},
                        {"homeAway": "away", "score": "1", "winner": True},
                    ],
                }
            ]
        }
        self.assertEqual(kicktipp_actual_score(event), (1, 2))


if __name__ == "__main__":
    unittest.main()
