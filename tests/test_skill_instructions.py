from __future__ import annotations

import unittest

from tests.helpers import ROOT


SKILL_DIR = ROOT / "skills" / "visual-prompt-cookbook"


class SkillInstructionTests(unittest.TestCase):
    def test_generation_offer_depends_on_agent_capability(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Do not ask whether to generate an image", skill_text)
        self.assertIn("current agent clearly has an image generation tool", skill_text)

    def test_skill_requires_explicit_invocation(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        openai_yaml = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("allow_implicit_invocation: false", openai_yaml)
        self.assertNotIn("allow_implicit_invocation: true", openai_yaml)
        self.assertIn("Invocation Policy", skill_text)
        self.assertIn("only when the user explicitly invokes it", skill_text)

    def test_description_does_not_advertise_generic_image_intent(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        description = skill_text.split("---")[1]

        self.assertIn("Explicit-invocation-only", description)
        self.assertIn("never select it on your own", description)
        for keyword in ("作图", "画图", "出图", "海报", "封面", "配图", "图片提示词"):
            self.assertNotIn(keyword, description)


if __name__ == "__main__":
    unittest.main()
