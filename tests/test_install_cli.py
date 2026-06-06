from __future__ import annotations

import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


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
            self.assertIn("Choose an agent", result.stdout)
            self.assertTrue((target_root / "visual-prompt-cookbook" / "SKILL.md").exists())

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
