from __future__ import annotations

import unittest
from datetime import datetime, timezone

from scripts.kicktipp_watchdog import format_tip_line, render_first_game_brief


class KickTippWatchdogFormattingTests(unittest.TestCase):
    def sample_row(self, *, match: str = "Ghana vs Panama", flags: list[str] | None = None, gain: float = 0.129) -> dict:
        return {
            "status": "ok",
            "match": match,
            "kickoff_utc": "2026-06-17T23:00Z",
            "source_risk_flags": flags or ["draw_signal", "low_edge", "big_home_move"],
            "final_pick": {"scoreline": "1:1", "p_gain_2plus": gain},
        }

    def test_tip_line_is_human_readable_not_raw_engine_speak(self) -> None:
        line = format_tip_line(self.sample_row())
        self.assertIn("Ghana vs Panama", line)
        self.assertIn("**1:1**", line)
        self.assertIn("⚖️ balanced market", line)
        self.assertIn("📈 market moved", line)
        for raw_token in ["controlled_attack", "gain≥2", "low_edge", "big_home_move", "["]:
            self.assertNotIn(raw_token, line)

    def test_first_game_brief_has_engaging_header_and_plain_badges(self) -> None:
        first = datetime(2026, 6, 17, 17, 0, tzinfo=timezone.utc)
        rows = [
            self.sample_row(match="Portugal vs Congo DR", flags=["low_edge", "big_away_move"], gain=0.0),
            self.sample_row(match="England vs Croatia", flags=["draw_signal", "low_edge"], gain=0.111),
        ]
        text = render_first_game_brief(rows, first)
        self.assertIn("🏆 KickTipp slate incoming", text)
        self.assertIn("First kickoff: **19:00**", text)
        self.assertIn("Selective miracle mode", text)
        self.assertIn("🧠 1 balanced market", text)
        for raw_token in ["controlled_attack", "gain≥2", "low_edge", "big_away_move"]:
            self.assertNotIn(raw_token, text)


if __name__ == "__main__":
    unittest.main()
