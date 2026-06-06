from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.helpers import load_script_module


core = load_script_module("cookbook_core")
dashboard_server = load_script_module("serve_dashboard")


class DashboardStateTests(unittest.TestCase):
    def test_normalize_dashboard_language_accepts_user_language(self) -> None:
        self.assertEqual(core.normalize_dashboard_language("zh-CN"), "zh-CN")
        self.assertEqual(core.normalize_dashboard_language("zh"), "zh-CN")
        self.assertEqual(core.normalize_dashboard_language("en-US"), "en")
        self.assertEqual(core.normalize_dashboard_language(None), "auto")
        self.assertEqual(core.normalize_dashboard_language("fr-FR"), "auto")

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

    def test_start_background_server_returns_url_and_opens_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = Path(tmp)
            process = Mock(pid=12345)
            with patch.object(dashboard_server, "find_available_port", return_value=54321):
                with patch.object(dashboard_server, "wait_for_server", return_value=True):
                    with patch.object(dashboard_server.subprocess, "Popen", return_value=process) as popen:
                        with patch.object(dashboard_server.webbrowser, "open") as open_browser:
                            url = dashboard_server.start_background_server(
                                host="127.0.0.1",
                                port=0,
                                skill_root=skill_root,
                                language="zh-CN",
                                open_browser=True,
                            )

            command = popen.call_args.args[0]
            self.assertEqual(url, "http://127.0.0.1:54321")
            self.assertIn("--foreground", command)
            self.assertIn("--no-open", command)
            self.assertTrue(popen.call_args.kwargs["start_new_session"])
            self.assertEqual((skill_root / ".dashboard-state" / "server.pid").read_text(encoding="utf-8"), "12345\n")
            open_browser.assert_called_once_with(url)

    def test_start_background_server_fails_when_child_does_not_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = Path(tmp)
            process = Mock(pid=12345)
            process.poll.return_value = 1
            with patch.object(dashboard_server, "find_available_port", return_value=54321):
                with patch.object(dashboard_server, "wait_for_server", return_value=False):
                    with patch.object(dashboard_server.subprocess, "Popen", return_value=process):
                        with self.assertRaisesRegex(RuntimeError, "Dashboard server failed to start"):
                            dashboard_server.start_background_server(
                                host="127.0.0.1",
                                port=0,
                                skill_root=skill_root,
                                language="zh-CN",
                                open_browser=False,
                            )


if __name__ == "__main__":
    unittest.main()
