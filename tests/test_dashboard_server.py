from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import load_script_module


core = load_script_module("cookbook_core")


class DashboardStateTests(unittest.TestCase):
    def test_record_selection_writes_jsonl_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            event = core.record_dashboard_selection(state_dir, {"style_slug": "mono-test-poster", "id": 1})
            events_path = state_dir / "events.jsonl"
            self.assertTrue(events_path.exists())
            saved = json.loads(events_path.read_text(encoding="utf-8").strip())
            self.assertEqual(saved["style_slug"], "mono-test-poster")
            self.assertEqual(saved["id"], 1)
            self.assertEqual(event["type"], "style_selected")

    def test_dashboard_paths_point_to_skill_assets(self) -> None:
        paths = core.dashboard_paths(Path("/skill"))
        self.assertEqual(paths["dashboard_root"], Path("/skill/assets/dashboard"))
        self.assertEqual(paths["cookbook_root"], Path("/skill/assets/cookbook"))


if __name__ == "__main__":
    unittest.main()
