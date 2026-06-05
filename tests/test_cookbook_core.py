from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import load_script_module


core = load_script_module("cookbook_core")


def sample_style() -> dict:
    return {
        "style_name": "Mono Test Poster",
        "style_slug": "mono-test-poster",
        "style_version": "2.1",
        "style_summary": "A sharp test poster style.",
        "environment_variables": {
            "SUBJECT": "main subject",
            "MAIN_TEXT": "headline",
            "ASPECT_RATIO": "image ratio",
        },
        "style_fidelity_anchors": ["large type", "mono palette"],
        "source_content_to_avoid": ["copied model", "source logo"],
        "negative_prompt": "no watermark",
        "prompt_template": (
            "Create a {ASPECT_RATIO} poster of {SUBJECT}. "
            "Headline: {MAIN_TEXT}. Anchors: {STYLE_FIDELITY_ANCHORS}. "
            "Avoid: {SOURCE_CONTENT_TO_AVOID}. Negative: {NEGATIVE_PROMPT}."
        ),
        "examples": [{"case_name": "demo", "values": {"SUBJECT": "architect"}}],
    }


class PromptRenderTests(unittest.TestCase):
    def test_extract_template_variables_returns_ordered_unique_names(self) -> None:
        names = core.extract_template_variables("{A} {B} {A} {STYLE_FIDELITY_ANCHORS}")
        self.assertEqual(names, ["A", "B", "STYLE_FIDELITY_ANCHORS"])

    def test_render_prompt_injects_special_style_fields(self) -> None:
        rendered = core.render_prompt(
            sample_style(),
            {
                "SUBJECT": "a tired architect",
                "MAIN_TEXT": "focus wins",
                "ASPECT_RATIO": "16:9",
            },
        )
        self.assertIn("a tired architect", rendered)
        self.assertIn("large type, mono palette", rendered)
        self.assertIn("copied model, source logo", rendered)
        self.assertIn("no watermark", rendered)
        self.assertNotIn("{", rendered)

    def test_render_prompt_reports_missing_template_variables(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing values: MAIN_TEXT"):
            core.render_prompt(sample_style(), {"SUBJECT": "a chef", "ASPECT_RATIO": "9:16"})


if __name__ == "__main__":
    unittest.main()


def write_sample_upstream(root: Path) -> None:
    style_dir = root / "styles" / "mono-test-poster"
    style_dir.mkdir(parents=True)
    (style_dir / "style.json").write_text(json.dumps(sample_style()), encoding="utf-8")
    (style_dir / "preview-16x9.jpg").write_bytes(b"preview16")
    (style_dir / "preview-9x16.jpg").write_bytes(b"preview9")
    schema_dir = root / "schemas"
    schema_dir.mkdir()
    (schema_dir / "style-v2.1.schema.json").write_text("{}", encoding="utf-8")
    (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")


class SyncIndexTests(unittest.TestCase):
    def test_sync_cookbook_copies_assets_and_builds_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "upstream"
            output = Path(tmp) / "assets" / "cookbook"
            source.mkdir()
            write_sample_upstream(source)

            result = core.sync_cookbook_assets(
                source_root=source,
                output_root=output,
                upstream_url="git@example.com:test/repo.git",
                commit_sha="abc123",
                synced_at="2026-06-05T00:00:00+00:00",
            )

            self.assertEqual(result["style_count"], 1)
            self.assertTrue((output / "LICENSE").exists())
            self.assertTrue((output / "schema" / "style-v2.1.schema.json").exists())
            self.assertTrue((output / "styles" / "mono-test-poster" / "style.json").exists())
            self.assertTrue((output / "styles-index.json").exists())
            index = json.loads((output / "styles-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["styles"][0]["id"], 1)
            self.assertEqual(index["styles"][0]["style_slug"], "mono-test-poster")
            self.assertEqual(index["styles"][0]["updated_from_commit"], "abc123")
