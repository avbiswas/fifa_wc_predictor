from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from worldcup_predictor.kicktipp_archive import archive_leverage_report, latest_archived_picks, scoreline_from_archived_record


class KickTippArchiveTests(unittest.TestCase):
    def sample_report(self) -> dict:
        return {
            "generated_at": "2026-06-16T10:00:00Z",
            "mode": "controlled_attack",
            "draw_budget": {"target": 2, "final_draws": 1},
            "current_state": {"deficit": 6},
            "rules": {"exact": 4, "tendency": 2},
            "source_status": {"espn": "ok"},
            "rows": [
                {
                    "status": "ok",
                    "event_id": "123",
                    "kickoff_utc": "2026-06-16T18:00:00Z",
                    "match": "France vs Senegal",
                    "home": "France",
                    "away": "Senegal",
                    "mode": "controlled_attack",
                    "final_pick": {"scoreline": "1:0", "pick": "home", "expected_points": 1.7},
                    "ev_pick": {"scoreline": "1:0", "expected_points": 1.7},
                    "odds_decimal": {"home": 1.9, "draw": 3.4, "away": 4.2},
                    "fair_probabilities": {"home": 0.51, "draw": 0.28, "away": 0.21},
                }
            ],
        }

    def test_archive_writes_report_ledger_and_latest_pre_kickoff_pick(self) -> None:
        with TemporaryDirectory() as tmp:
            result = archive_leverage_report(self.sample_report(), tmp)
            self.assertEqual(result["records_written"], 1)
            self.assertEqual(result["eligible_records"], 1)
            self.assertTrue(Path(result["snapshot_path"]).exists())
            ledger = Path(result["ledger_path"])
            records = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["final_tip"], "1:0")

            latest = latest_archived_picks(tmp)
            self.assertIn("event-123", latest)
            self.assertEqual(scoreline_from_archived_record(latest["event-123"]), (1, 0))

    def test_archive_does_not_mark_post_kickoff_pick_as_backtest_eligible(self) -> None:
        report = self.sample_report()
        report["generated_at"] = "2026-06-16T19:00:00Z"
        with TemporaryDirectory() as tmp:
            result = archive_leverage_report(report, tmp)
            self.assertEqual(result["records_written"], 1)
            self.assertEqual(result["eligible_records"], 0)
            self.assertEqual(latest_archived_picks(tmp), {})


if __name__ == "__main__":
    unittest.main()
