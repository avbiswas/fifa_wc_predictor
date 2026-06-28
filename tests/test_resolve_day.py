from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from worldcup_predictor.models import competition_aliases
from worldcup_predictor.resolve_day import (
    assign_third_place_groups,
    chronological_match_numbers,
    main,
    matches_in_prediction_window,
    missing_prediction_aliases,
    resolve_day,
    resolve_knockout_fixtures,
    result_retry_pending,
    unresolved_past_matches,
)


def match(match_id: int, kickoff: str) -> dict:
    return {
        "match_id": str(match_id),
        "kickoff_utc": kickoff,
        "team1": f"Team {match_id}A",
        "team2": f"Team {match_id}B",
        "team1_code": "AAA",
        "team2_code": "BBB",
        "round": "Matchday 1",
    }


def result(match_id: int, team1: str, team2: str, team1_score: int, team2_score: int) -> dict:
    return {
        "match_id": match_id,
        "team1": team1,
        "team2": team2,
        "team1_score": team1_score,
        "team2_score": team2_score,
        "winner": team1 if team1_score > team2_score else team2 if team2_score > team1_score else "Draw",
        "goals": [],
    }


class ResolveDayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 6, 12, 0, 0, tzinfo=timezone.utc)

    def test_prediction_window_is_future_only_and_capped_at_24_hours(self) -> None:
        schedule = [
            match(1, "2026-06-11T23:59:59Z"),
            match(2, "2026-06-12T00:00:01Z"),
            match(3, "2026-06-13T00:00:00Z"),
            match(4, "2026-06-13T00:00:01Z"),
        ]
        self.assertEqual(
            [int(row["match_id"]) for row in matches_in_prediction_window(schedule, self.now)],
            [2, 3],
        )

    def test_chronological_number_differs_from_internal_id(self) -> None:
        schedule = [
            match(1, "2026-06-11T19:00:00Z"),
            match(2, "2026-06-12T02:00:00Z"),
            match(7, "2026-06-12T19:00:00Z"),
        ]
        self.assertEqual(chronological_match_numbers(schedule)[7], 3)

    def test_only_missing_past_results_are_selected(self) -> None:
        schedule = [
            match(1, "2026-06-11T20:00:00Z"),
            match(2, "2026-06-11T21:00:00Z"),
            match(3, "2026-06-12T01:00:00Z"),
        ]
        store = {"results": {"1": {"match_id": 1}}}
        self.assertEqual(
            [int(row["match_id"]) for row in unresolved_past_matches(store, schedule, self.now)],
            [2],
        )

    def test_unresolved_knockout_placeholders_are_not_selected(self) -> None:
        schedule = [
            {
                **match(73, "2026-06-12T01:00:00Z"),
                "round": "Round of 32",
                "team1": "2A",
                "team2": "2B",
                "team1_code": "",
                "team2_code": "",
                "group": "",
            }
        ]
        self.assertEqual(matches_in_prediction_window(schedule, self.now), [])
        self.assertEqual(unresolved_past_matches({}, schedule, self.now), [])

    def test_completed_group_resolves_knockout_placeholder(self) -> None:
        schedule = [
            {
                **match(1, "2026-06-11T19:00:00Z"),
                "group": "Group A",
                "team1": "Alpha",
                "team2": "Beta",
                "team1_code": "ALP",
                "team2_code": "BET",
            },
            {
                **match(2, "2026-06-11T21:00:00Z"),
                "group": "Group A",
                "team1": "Gamma",
                "team2": "Delta",
                "team1_code": "GAM",
                "team2_code": "DEL",
            },
            {
                **match(73, "2026-06-12T01:00:00Z"),
                "round": "Round of 32",
                "team1": "1A",
                "team2": "2A",
                "team1_code": "",
                "team2_code": "",
                "group": "",
            },
        ]
        store = {
            "results": {
                "1": result(1, "Alpha", "Beta", 2, 0),
                "2": result(2, "Gamma", "Delta", 1, 0),
            }
        }

        resolved, updates = resolve_knockout_fixtures(store, schedule)

        self.assertEqual(resolved[2]["team1"], "Alpha")
        self.assertEqual(resolved[2]["team2"], "Gamma")
        self.assertEqual(resolved[2]["team1_code"], "ALP")
        self.assertEqual(resolved[2]["team2_code"], "GAM")
        self.assertEqual(updates[0]["to"], "Alpha vs Gamma")

    def test_current_third_place_combination_uses_annex_c_routing(self) -> None:
        slots = [
            {"match_id": "74", "team1": "1E", "team2": "3A/B/C/D/F"},
            {"match_id": "77", "team1": "1I", "team2": "3C/D/F/G/H"},
            {"match_id": "79", "team1": "1A", "team2": "3C/E/F/H/I"},
            {"match_id": "80", "team1": "1L", "team2": "3E/H/I/J/K"},
            {"match_id": "81", "team1": "1D", "team2": "3B/E/F/I/J"},
            {"match_id": "82", "team1": "1G", "team2": "3A/E/H/I/J"},
            {"match_id": "85", "team1": "1B", "team2": "3E/F/G/I/J"},
            {"match_id": "87", "team1": "1K", "team2": "3D/E/I/J/L"},
        ]

        self.assertEqual(
            assign_third_place_groups(["K", "F", "E", "L", "B", "J", "D", "I"], slots),
            {
                "3A/B/C/D/F": "D",
                "3C/D/F/G/H": "F",
                "3C/E/F/H/I": "E",
                "3E/H/I/J/K": "K",
                "3B/E/F/I/J": "B",
                "3A/E/H/I/J": "I",
                "3E/F/G/I/J": "J",
                "3D/E/I/J/L": "L",
            },
        )

    def test_completed_predictions_have_no_missing_aliases(self) -> None:
        fixture = match(1, "2026-06-12T01:00:00Z")
        store = {
            "predictions": [
                {"match_id": 1, "model_alias": alias}
                for alias in competition_aliases()
            ]
        }
        self.assertEqual(missing_prediction_aliases(store, 1, fixture), [])

    def test_result_retry_blocks_immediate_repeat(self) -> None:
        store = {
            "resolution_state": {
                "result_attempts": {
                    "1": {"retry_after": "2026-06-12T01:00:00Z"}
                }
            }
        }
        self.assertTrue(result_retry_pending(store, 1, self.now))
        self.assertFalse(
            result_retry_pending(
                store,
                1,
                datetime(2026, 6, 12, 1, 0, tzinfo=timezone.utc),
            )
        )

    @patch("worldcup_predictor.resolve_day.fetch_match_result")
    @patch("worldcup_predictor.resolve_day.run_predictions_async")
    @patch("worldcup_predictor.resolve_day.write_prediction_store")
    def test_noop_rerun_makes_no_external_calls(self, write_store, run_model, fetch_result) -> None:
        fixture = match(1, "2026-06-11T20:00:00Z")
        store = {
            "results": {
                "1": {
                    "match_id": 1,
                    "team1_score": 1,
                    "team2_score": 0,
                    "winner": "Team 1A",
                    "goals": [],
                }
            },
            "predictions": [
                {
                    "match_id": 1,
                    "model_alias": alias,
                    "prediction": "Team 1A",
                    "scoreline": "Team 1A 1-0 Team 1B",
                    "goal_scorers": [],
                }
                for alias in competition_aliases()
            ],
        }
        resolve_day(store, [fixture], self.now, news_results=5, dry_run=False)
        first_leaderboard = store["leaderboard"].copy()
        resolve_day(store, [fixture], self.now, news_results=5, dry_run=False)

        run_model.assert_not_called()
        fetch_result.assert_not_called()
        self.assertEqual(store["leaderboard"], first_leaderboard)
        self.assertEqual(write_store.call_count, 1)

    @patch("worldcup_predictor.resolve_day.resolve_day")
    @patch("worldcup_predictor.resolve_day.load_prediction_store", return_value={})
    @patch("worldcup_predictor.resolve_day.read_csv", return_value=[])
    @patch("builtins.input", side_effect=["n", "n", "n"])
    def test_cli_rejection_stops_after_planning(self, input_mock, read_csv_mock, load_store_mock, resolve_mock) -> None:
        resolve_mock.return_value = {
            "resolved_at": "2026-06-12T00:00:00Z",
            "predictions_run": [
                {"match_id": 7, "match_number": 3, "match": "A vs B", "models": ["one"]},
                {"match_id": 19, "match_number": 4, "match": "C vs D", "models": ["one"]},
            ],
            "predictions_skipped": [],
            "results_fetched": [{"match_id": 1, "match": "E vs F"}],
            "results_skipped": [],
            "prediction_failures": [],
            "result_failures": [],
        }
        with patch("sys.argv", ["resolve_day"]):
            self.assertEqual(main(), 0)
        resolve_mock.assert_called_once()
        self.assertTrue(resolve_mock.call_args.kwargs["dry_run"])

    @patch("worldcup_predictor.resolve_day.resolve_day")
    @patch("worldcup_predictor.resolve_day.load_prediction_store", return_value={})
    @patch("worldcup_predictor.resolve_day.read_csv", return_value=[])
    @patch("builtins.input", side_effect=["y", "y", "n"])
    def test_cli_approvals_are_case_insensitive_and_split_by_action(
        self,
        input_mock,
        read_csv_mock,
        load_store_mock,
        resolve_mock,
    ) -> None:
        plan = {
            "resolved_at": "2026-06-12T00:00:00Z",
            "predictions_run": [
                {"match_id": 7, "match_number": 3, "match": "A vs B", "models": ["one"]},
                {"match_id": 19, "match_number": 4, "match": "C vs D", "models": ["one"]},
            ],
            "predictions_skipped": [],
            "results_fetched": [{"match_id": 1, "match": "E vs F"}],
            "results_skipped": [],
            "prediction_failures": [],
            "result_failures": [],
        }
        completed = {"prediction_failures": [], "result_failures": []}
        resolve_mock.side_effect = [plan, completed]
        with patch("sys.argv", ["resolve_day"]):
            self.assertEqual(main(), 0)
        self.assertEqual(resolve_mock.call_count, 2)
        self.assertTrue(resolve_mock.call_args_list[0].kwargs["dry_run"])
        execution = resolve_mock.call_args_list[1].kwargs
        self.assertFalse(execution["dry_run"])
        self.assertTrue(execution["fetch_results"])
        self.assertEqual(execution["selected_prediction_match_ids"], {7})


if __name__ == "__main__":
    unittest.main()
