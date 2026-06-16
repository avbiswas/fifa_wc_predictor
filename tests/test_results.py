from __future__ import annotations

import unittest
from unittest.mock import patch

from worldcup_predictor.results import fetch_match_result


class ResultFetchFallbackTests(unittest.TestCase):
    @patch("worldcup_predictor.results.get_match")
    @patch("worldcup_predictor.results._get_json")
    def test_worldcup_feed_fallback_handles_schedule_id_mismatch(self, get_json, get_match) -> None:
        get_match.return_value = {"team1": "Iran", "team2": "New Zealand"}
        get_json.side_effect = [
            {"events": []},
            {
                "games": [
                    {
                        "id": "13",
                        "home_team_name_en": "Iran",
                        "away_team_name_en": "New Zealand",
                        "home_score": "2",
                        "away_score": "2",
                        "home_scorers": "{\"Ramin Rzaiian 32'\",\"Mohamed Mhbi 64'\"}",
                        "away_scorers": "{\"Ali Jast 7'\",\"Ali Jast 54'\"}",
                        "finished": "TRUE",
                        "time_elapsed": "finished",
                    }
                ]
            },
        ]

        result = fetch_match_result(38)

        self.assertEqual(result["fixture_id"], 13)
        self.assertEqual(result["provider"], "worldcup26.ir")
        self.assertEqual(result["team1_score"], 2)
        self.assertEqual(result["team2_score"], 2)
        self.assertEqual(result["winner"], "Draw")
        self.assertEqual([goal["scorer"] for goal in result["goals"]], ["Ramin Rzaiian", "Mohamed Mhbi", "Ali Jast", "Ali Jast"])


if __name__ == "__main__":
    unittest.main()