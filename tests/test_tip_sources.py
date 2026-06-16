from __future__ import annotations

from datetime import datetime, timezone
import unittest

from worldcup_predictor.tip_sources import date_range, form_points, normalize_team_name, parse_espn_odds


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


if __name__ == "__main__":
    unittest.main()
