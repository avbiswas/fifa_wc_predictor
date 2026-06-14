from __future__ import annotations

import argparse
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_model_roster.py"

spec = importlib.util.spec_from_file_location("run_model_roster", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
run_model_roster = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_model_roster)


class RunModelRosterTests(unittest.TestCase):
    def test_command_preserves_per_entry_default_provider(self) -> None:
        args = argparse.Namespace(days=3, tz="Europe/Berlin", future_only=False, force=False, dry_run=True)
        command = run_model_roster.command_for(args, {"model": "m1", "provider": None})
        self.assertIn("--hermes-model", command)
        self.assertIn("m1", command)
        self.assertNotIn("--hermes-provider", command)

    def test_command_preserves_explicit_provider_pairing(self) -> None:
        args = argparse.Namespace(days=3, tz="Europe/Berlin", future_only=True, force=True, dry_run=True)
        command = run_model_roster.command_for(args, {"model": "m2", "provider": "p2"})
        self.assertIn("--hermes-model", command)
        self.assertIn("m2", command)
        self.assertIn("--hermes-provider", command)
        self.assertIn("p2", command)
        self.assertIn("--future-only", command)
        self.assertIn("--force", command)


if __name__ == "__main__":
    unittest.main()
