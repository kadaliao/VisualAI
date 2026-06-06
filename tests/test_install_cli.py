from __future__ import annotations

import http.client
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from visualai import install_skill


class InstallCliTests(unittest.TestCase):
    def test_project_command_installs_skill_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            skills_root = root / "skills"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "custom",
                    "--source-root",
                    str(source),
                    "--target-root",
                    str(skills_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Installed visual-prompt-cookbook", result.stdout)
            self.assertTrue((skills_root / "visual-prompt-cookbook" / "scripts" / "tool.py").exists())

    def test_project_command_installs_selected_agent_to_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            target_root = root / "codex-skills"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "codex",
                    "--source-root",
                    str(source),
                    "--target-root",
                    str(target_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Codex", result.stdout)
            self.assertTrue((target_root / "visual-prompt-cookbook" / "SKILL.md").exists())

    def test_project_command_installs_gemini_extension_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            target_root = root / "gemini-extensions"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "gemini",
                    "--source-root",
                    str(source),
                    "--target-root",
                    str(target_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            extension = target_root / "visual-prompt-cookbook"
            installed = extension / "skills" / "visual-prompt-cookbook"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((extension / "gemini-extension.json").exists())
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((installed / "scripts" / "tool.py").exists())

    def test_project_command_installs_hermes_to_default_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            home = root / "home"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "hermes",
                    "--source-root",
                    str(source),
                    "--home",
                    str(home),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            installed = home / ".hermes" / "skills" / "visual-prompt-cookbook"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Hermes Agent", result.stdout)
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((installed / "scripts" / "tool.py").exists())

    def test_project_command_installs_all_known_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            home = root / "home"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "all",
                    "--source-root",
                    str(source),
                    "--home",
                    str(home),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".codex" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())
            self.assertTrue((home / ".claude" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())
            self.assertTrue((home / ".cursor" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())
            self.assertTrue((home / ".config" / "opencode" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())
            self.assertTrue(
                (home / ".codeium" / "windsurf" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists()
            )
            self.assertTrue(
                (home / ".openclaw-autoclaw" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists()
            )
            self.assertTrue((home / ".hermes" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())
            self.assertTrue(
                (
                    home
                    / ".gemini"
                    / "extensions"
                    / "visual-prompt-cookbook"
                    / "skills"
                    / "visual-prompt-cookbook"
                    / "SKILL.md"
                ).exists()
            )

    def test_project_command_lists_agents(self) -> None:
        result = subprocess.run(
            ["uv", "run", "visualai-install", "--list-agents"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codex", result.stdout)
        self.assertIn("claude", result.stdout)
        self.assertIn("gemini", result.stdout)
        self.assertIn("hermes", result.stdout)
        self.assertIn("all", result.stdout)

    def test_project_command_interactively_selects_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            target_root = root / "claude-skills"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--source-root",
                    str(source),
                    "--target-root",
                    str(target_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                input="claude\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Install visual-prompt-cookbook", result.stdout)
            self.assertIn("Choose an agent", result.stdout)
            self.assertIn("1. Codex", result.stdout)
            self.assertIn("Claude Code", result.stdout)
            self.assertTrue((target_root / "visual-prompt-cookbook" / "SKILL.md").exists())

    def test_project_command_interactively_selects_agent_by_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            target_root = root / "claude-skills"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--source-root",
                    str(source),
                    "--target-root",
                    str(target_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                input="2\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Installed visual-prompt-cookbook for Claude Code", result.stdout)
            self.assertTrue((target_root / "visual-prompt-cookbook" / "SKILL.md").exists())

    def test_project_command_interactively_selects_custom_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skill"
            target_root = root / "custom-skills"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--source-root",
                    str(source),
                ],
                cwd=Path(__file__).resolve().parents[1],
                input=f"10\n{target_root}\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Custom skill directory", result.stdout)
            self.assertTrue((target_root / "visual-prompt-cookbook" / "SKILL.md").exists())

    def test_project_command_reports_archive_progress_after_interactive_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "visualai.zip"
            home = root / "home"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("VisualAI-main/skills/visual-prompt-cookbook/SKILL.md", "---\nname: demo\n---\n")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--archive-url",
                    archive_path.as_uri(),
                    "--home",
                    str(home),
                ],
                cwd=Path(__file__).resolve().parents[1],
                input="2\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Downloading skill package", result.stdout)
            self.assertIn("[", result.stdout)
            self.assertIn("100%", result.stdout)
            self.assertIn("Installing for Claude Code", result.stdout)
            self.assertTrue((home / ".claude" / "skills" / "visual-prompt-cookbook" / "SKILL.md").exists())

    def test_project_dependencies_include_tqdm_and_questionary(self) -> None:
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("tqdm", pyproject)
        self.assertIn("simple-term-menu", pyproject)
        self.assertNotIn("questionary", pyproject)

    def test_download_uses_tqdm_progress_bar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = Mock()
            response.headers = {"length": "1"}
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)

            with patch.object(install_skill.urllib.request, "urlopen", return_value=response):
                with patch.object(install_skill.tqdm.tqdm, "wrapattr") as wrapattr:
                    wrapped = Mock()
                    wrapped.__enter__ = Mock(return_value=Mock(read=Mock(side_effect=[b"x", b""])))
                    wrapped.__exit__ = Mock(return_value=False)
                    wrapattr.return_value = wrapped
                    with patch.object(install_skill.shutil, "copyfileobj"):
                        install_skill.download_archive("https://example.test/archive.zip", root / "archive.zip", verbose=True)

            wrapattr.assert_called_once()
            self.assertEqual(wrapattr.call_args.kwargs["desc"], "Downloading skill package")

    def test_interactive_tty_agent_menu_uses_term_menu(self) -> None:
        with patch.object(install_skill.sys.stdin, "isatty", return_value=True):
            with patch.object(install_skill, "TerminalMenu") as terminal_menu:
                terminal_menu.return_value.show.return_value = 1

                selected = install_skill.choose_agent_interactively()

        self.assertEqual(selected, "claude")
        terminal_menu.assert_called_once()

    def test_download_retries_after_incomplete_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = 0

            def download(_: str, filename: Path, verbose: bool = False):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise http.client.IncompleteRead(b"partial")
                with zipfile.ZipFile(filename, "w") as archive:
                    archive.writestr("VisualAI-main/skills/visual-prompt-cookbook/SKILL.md", "---\nname: demo\n---\n")

            with patch.object(install_skill, "download_archive", side_effect=download):
                source_root = install_skill.download_skill_root("https://example.test/archive.zip", root, verbose=False)

            self.assertEqual(calls, 2)
            self.assertTrue((source_root / "SKILL.md").exists())

    def test_cli_reports_download_failure_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            helper = Path(tmp) / "fail_urlretrieve.py"
            helper.write_text(
                "\n".join(
                    [
                        "import http.client",
                        "import sys",
                        "import urllib.request",
                        "from visualai import install_skill",
                        "",
                        "def fail(*args, **kwargs):",
                        "    raise http.client.IncompleteRead(b'partial')",
                        "",
                        "urllib.request.urlretrieve = fail",
                        "sys.argv = ['visualai-install', '--agent', 'codex', '--archive-url', 'https://example.test/archive.zip', '--home', sys.argv[1]]",
                        "install_skill.main()",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["uv", "run", "python", str(helper), str(Path(tmp) / "home")],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Failed to download skill package", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_reports_bad_archive_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "broken.zip"
            archive_path.write_bytes(b"not a zip")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "codex",
                    "--archive-url",
                    archive_path.as_uri(),
                    "--home",
                    str(root / "home"),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Downloaded archive is not a valid zip file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_custom_agent_requires_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source-skill"
            (source / "scripts").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "custom",
                    "--source-root",
                    str(source),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--target-root", result.stderr)

    def test_project_command_installs_from_source_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "visualai.zip"
            skills_root = root / "skills"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("VisualAI-main/skills/visual-prompt-cookbook/SKILL.md", "---\nname: demo\n---\n")
                archive.writestr(
                    "VisualAI-main/skills/visual-prompt-cookbook/scripts/tool.py",
                    "print('ok')",
                )
                archive.writestr(
                    "VisualAI-main/skills/visual-prompt-cookbook/.dashboard-state/events.jsonl",
                    "{}",
                )

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "visualai-install",
                    "--agent",
                    "custom",
                    "--archive-url",
                    archive_path.as_uri(),
                    "--target-root",
                    str(skills_root),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            installed = skills_root / "visual-prompt-cookbook"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Installed visual-prompt-cookbook", result.stdout)
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((installed / "scripts" / "tool.py").exists())
            self.assertFalse((installed / ".dashboard-state").exists())


if __name__ == "__main__":
    unittest.main()
