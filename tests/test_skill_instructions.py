from __future__ import annotations

import unittest

from tests.helpers import ROOT


class SkillInstructionTests(unittest.TestCase):
    def test_generation_offer_depends_on_agent_capability(self) -> None:
        skill_text = (ROOT / "skills" / "visual-prompt-cookbook" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Do not ask whether to generate an image", skill_text)
        self.assertIn("current agent clearly has an image generation tool", skill_text)


if __name__ == "__main__":
    unittest.main()
