from __future__ import annotations

import unittest

from worldcup_predictor.bonus_optimizer import BonusOption, optimize_bonus_questions, select_bonus_answers


class BonusOptimizerTests(unittest.TestCase):
    def test_selects_probability_core_plus_contrarian_slot(self) -> None:
        options = [
            BonusOption("Obvious A", probability=0.60, ownership=0.90),
            BonusOption("Obvious B", probability=0.50, ownership=0.80),
            BonusOption("Live Outsider", probability=0.28, ownership=0.15),
            BonusOption("Trash Punt", probability=0.04, ownership=0.02),
        ]
        selected = select_bonus_answers(options, slots=3, mode="controlled_attack", contrarian_slots=1)
        labels = {row.label for row in selected}
        self.assertIn("Live Outsider", labels)
        self.assertIn("Obvious A", labels)
        self.assertNotIn("Trash Punt", labels)

    def test_safe_mode_does_not_force_contrarian_answer(self) -> None:
        options = [
            BonusOption("Obvious A", probability=0.60, ownership=0.90),
            BonusOption("Obvious B", probability=0.50, ownership=0.80),
            BonusOption("Outsider", probability=0.20, ownership=0.10),
        ]
        selected = select_bonus_answers(options, slots=2, mode="safe")
        self.assertEqual([row.label for row in selected], ["Obvious A", "Obvious B"])

    def test_optimize_bonus_questions_handles_empty_template(self) -> None:
        report = optimize_bonus_questions({"questions": []})
        self.assertEqual(report["questions"], [])

    def test_optimize_bonus_questions_parses_percent_inputs(self) -> None:
        report = optimize_bonus_questions(
            {
                "questions": [
                    {
                        "id": "winner",
                        "slots": 1,
                        "points": 4,
                        "options": [
                            {"label": "A", "probability": 60, "ownership": 90},
                            {"label": "B", "probability": 35, "ownership": 20},
                        ],
                    }
                ]
            },
            mode="controlled_attack",
        )
        self.assertEqual(report["questions"][0]["selected"][0]["label"], "A")
        self.assertAlmostEqual(report["questions"][0]["ranked_options"][0]["probability"], 0.6)


if __name__ == "__main__":
    unittest.main()
