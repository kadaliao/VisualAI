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
                    "visualai-install-skill",
                    "--source-root",
                    str(source),
                    "--skills-root",
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
                    "visualai-install-skill",
                    "--archive-url",
                    archive_path.as_uri(),
                    "--skills-root",
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
