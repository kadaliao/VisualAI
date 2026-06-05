# Visual Prompt Cookbook Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a maintainable Codex skill that syncs AI Visual Prompt Cookbook styles, serves a local dashboard, renders final prompts from selected styles, and installs itself to the user's local skills folder.

**Architecture:** Keep all runtime code bundled inside `skills/visual-prompt-cookbook` so the installed skill works independently of the source repo. Use small Python stdlib scripts for sync, indexing, prompt rendering, serving the dashboard, and installation. Keep the dashboard as no-build static HTML/CSS/JS backed by a local Python HTTP server and JSON assets.

**Tech Stack:** Python 3 stdlib, `uv run python`, `unittest`, static HTML/CSS/JS, Codex skill `SKILL.md` + `agents/openai.yaml`.

---

## File Structure

- Create `pyproject.toml`: project metadata and unittest-oriented test settings.
- Create `README.md`: short Chinese usage notes for source maintenance.
- Create `skills/visual-prompt-cookbook/SKILL.md`: Codex skill trigger and workflow instructions.
- Create `skills/visual-prompt-cookbook/agents/openai.yaml`: UI metadata.
- Create `skills/visual-prompt-cookbook/references/usage-workflow.md`: longer workflow reference loaded only when needed.
- Create `skills/visual-prompt-cookbook/scripts/cookbook_core.py`: shared sync, index, render, and install helpers.
- Create `skills/visual-prompt-cookbook/scripts/sync_cookbook.py`: CLI for syncing upstream assets and rebuilding the index.
- Create `skills/visual-prompt-cookbook/scripts/render_prompt.py`: CLI for rendering prompts from a style and variable JSON.
- Create `skills/visual-prompt-cookbook/scripts/serve_dashboard.py`: CLI for the local dashboard server.
- Create `skills/visual-prompt-cookbook/scripts/install_skill.py`: CLI for copying the skill into `~/.codex/skills`.
- Create `skills/visual-prompt-cookbook/assets/dashboard/index.html`: dashboard shell.
- Create `skills/visual-prompt-cookbook/assets/dashboard/app.js`: dashboard search, detail, and selection UI.
- Create `skills/visual-prompt-cookbook/assets/dashboard/styles.css`: dashboard styling.
- Create `tests/helpers.py`: import helpers for bundled skill scripts.
- Create `tests/test_cookbook_core.py`: tests for index, sync, prompt rendering, and install helpers.
- Create `tests/test_dashboard_server.py`: tests for dashboard route helpers and selection recording.

## Task 1: Project Skeleton and Core Prompt Renderer

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `skills/visual-prompt-cookbook/scripts/cookbook_core.py`
- Create: `tests/helpers.py`
- Create: `tests/test_cookbook_core.py`

- [ ] **Step 1: Write failing tests for prompt rendering helpers**

Create `tests/helpers.py`:

```python
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "visual-prompt-cookbook" / "scripts"


def load_script_module(name: str) -> ModuleType:
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

Create the initial `tests/test_cookbook_core.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail because core module is missing**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core -v
```

Expected: error mentioning `cookbook_core.py` does not exist.

- [ ] **Step 3: Add minimal project metadata and core implementation**

Create `pyproject.toml`:

```toml
[project]
name = "visualai"
version = "0.1.0"
description = "Local Codex skill source for AI visual prompt workflows."
requires-python = ">=3.11"
dependencies = []

[tool.uv]
package = false
```

Create `README.md`:

```markdown
# VisualAI

这个仓库维护一个本地 Codex skill：`visual-prompt-cookbook`。

第一版目标：

- 从 `kadaliao/AI-Visual-Prompt-Cookbook` 同步风格 JSON 和预览图。
- Serve 本地 dashboard，帮助用户浏览和选择风格。
- 让 Codex 主动补全变量，并默认输出最终可用提示词。
- 用户明确要求生成图片时，再把提示词交给图像生成能力。

Python 命令统一使用 `uv run python`。
```

Create `skills/visual-prompt-cookbook/scripts/cookbook_core.py`:

```python
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from string import Formatter
from typing import Any


SPECIAL_TEMPLATE_VALUES = {
    "STYLE_FIDELITY_ANCHORS": "style_fidelity_anchors",
    "SOURCE_CONTENT_TO_AVOID": "source_content_to_avoid",
    "NEGATIVE_PROMPT": "negative_prompt",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extract_template_variables(template: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if not field_name:
            continue
        name = field_name.split(".", 1)[0].split("[", 1)[0]
        if re.fullmatch(r"[A-Z0-9_]+", name) and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _format_special_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def render_prompt(style: dict[str, Any], values: dict[str, str]) -> str:
    template = style["prompt_template"]
    merged: dict[str, str] = {key: str(value) for key, value in values.items()}
    for template_name, style_key in SPECIAL_TEMPLATE_VALUES.items():
        if style_key in style and template_name not in merged:
            merged[template_name] = _format_special_value(style[style_key])

    required = extract_template_variables(template)
    missing = [name for name in required if not merged.get(name)]
    if missing:
        raise ValueError(f"Missing values: {', '.join(missing)}")

    rendered = template.format(**merged)
    leftovers = extract_template_variables(rendered)
    if leftovers:
        raise ValueError(f"Unresolved placeholders: {', '.join(leftovers)}")
    return rendered
```

- [ ] **Step 4: Run tests and verify Task 1 passes**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add pyproject.toml README.md tests/helpers.py tests/test_cookbook_core.py skills/visual-prompt-cookbook/scripts/cookbook_core.py
git commit -m "feat: add visual prompt core renderer"
```

## Task 2: Cookbook Sync and Index Builder

**Files:**
- Modify: `skills/visual-prompt-cookbook/scripts/cookbook_core.py`
- Create: `skills/visual-prompt-cookbook/scripts/sync_cookbook.py`
- Modify: `tests/test_cookbook_core.py`

- [ ] **Step 1: Add failing tests for syncing a synthetic upstream tree**

Append to `tests/test_cookbook_core.py`:

```python
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
```

- [ ] **Step 2: Run the new test and verify it fails because sync helper is missing**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core.SyncIndexTests -v
```

Expected: fail with `AttributeError` for `sync_cookbook_assets`.

- [ ] **Step 3: Implement sync and index helpers**

Append these functions to `cookbook_core.py`:

```python
def default_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_cookbook_root() -> Path:
    return default_skill_root() / "assets" / "cookbook"


def style_tags(style: dict[str, Any]) -> list[str]:
    text = f"{style.get('style_name', '')} {style.get('style_summary', '')}".lower()
    rules = [
        ("poster", ["poster", "海报"]),
        ("fashion", ["fashion", "editorial", "时尚"]),
        ("product", ["product", "ad", "广告", "launch"]),
        ("collage", ["collage", "zine", "doodle", "拼贴"]),
        ("photo", ["photo", "photographic", "摄影"]),
        ("typography", ["type", "typography", "letter", "字体"]),
        ("travel", ["travel", "city", "urban", "旅行", "城市"]),
        ("food", ["food", "beverage", "drink", "食物"]),
    ]
    tags = [tag for tag, needles in rules if any(needle in text for needle in needles)]
    return tags or ["visual"]


def build_styles_index(cookbook_root: Path, upstream: dict[str, Any]) -> dict[str, Any]:
    styles_root = cookbook_root / "styles"
    entries: list[dict[str, Any]] = []
    for index, style_path in enumerate(sorted(styles_root.glob("*/style.json")), start=1):
        style = read_json(style_path)
        slug = style["style_slug"]
        entries.append(
            {
                "id": index,
                "style_name": style["style_name"],
                "style_slug": slug,
                "style_summary": style["style_summary"],
                "preview_16x9": f"styles/{slug}/preview-16x9.jpg",
                "preview_9x16": f"styles/{slug}/preview-9x16.jpg",
                "environment_variables": list(style.get("environment_variables", {}).keys()),
                "tags": style_tags(style),
                "updated_from_commit": upstream["commit_sha"],
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "upstream": upstream,
        "style_count": len(entries),
        "styles": entries,
    }


def sync_cookbook_assets(
    *,
    source_root: Path,
    output_root: Path,
    upstream_url: str,
    commit_sha: str,
    synced_at: str | None = None,
) -> dict[str, Any]:
    if not (source_root / "styles").is_dir():
        raise FileNotFoundError(f"Missing upstream styles directory: {source_root / 'styles'}")
    if output_root.exists():
        shutil.rmtree(output_root)
    (output_root / "styles").mkdir(parents=True)

    style_count = 0
    for style_json in sorted((source_root / "styles").glob("*/style.json")):
        slug = style_json.parent.name
        target_dir = output_root / "styles" / slug
        target_dir.mkdir(parents=True)
        for name in ("style.json", "preview-16x9.jpg", "preview-9x16.jpg"):
            source_file = style_json.parent / name
            if not source_file.exists():
                raise FileNotFoundError(f"Missing required style asset: {source_file}")
            shutil.copy2(source_file, target_dir / name)
        style_count += 1

    schema_source = source_root / "schemas" / "style-v2.1.schema.json"
    if schema_source.exists():
        (output_root / "schema").mkdir()
        shutil.copy2(schema_source, output_root / "schema" / schema_source.name)
    license_source = source_root / "LICENSE"
    if license_source.exists():
        shutil.copy2(license_source, output_root / "LICENSE")

    upstream = {
        "upstream_url": upstream_url,
        "commit_sha": commit_sha,
        "synced_at": synced_at or utc_now_iso(),
        "style_count": style_count,
        "schema_path": "schema/style-v2.1.schema.json",
        "license": "MIT",
    }
    write_json(output_root / "upstream.json", upstream)
    write_json(output_root / "styles-index.json", build_styles_index(output_root, upstream))
    write_json(output_root / "manifest.json", {"style_count": style_count, "upstream": upstream})
    return upstream
```

- [ ] **Step 4: Add `sync_cookbook.py` CLI**

Create `skills/visual-prompt-cookbook/scripts/sync_cookbook.py`:

```python
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from cookbook_core import default_cookbook_root, sync_cookbook_assets


DEFAULT_REPO_URL = "git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git"


def git_commit_sha(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def clone_upstream(repo_url: str, target: Path) -> Path:
    checkout = target / "AI-Visual-Prompt-Cookbook"
    subprocess.check_call(["git", "clone", "--depth", "1", repo_url, str(checkout)])
    return checkout


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync AI Visual Prompt Cookbook assets into this skill.")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--source-dir", type=Path, help="Use an existing local Cookbook checkout.")
    parser.add_argument("--output-dir", type=Path, default=default_cookbook_root())
    parser.add_argument("--commit-sha", help="Commit SHA to record when --source-dir is not a git checkout.")
    args = parser.parse_args()

    if args.source_dir:
        source = args.source_dir.resolve()
        try:
            commit_sha = args.commit_sha or git_commit_sha(source)
        except subprocess.CalledProcessError:
            commit_sha = args.commit_sha or "local-source"
        upstream_url = args.repo_url
        result = sync_cookbook_assets(
            source_root=source,
            output_root=args.output_dir.resolve(),
            upstream_url=upstream_url,
            commit_sha=commit_sha,
        )
    else:
        with tempfile.TemporaryDirectory() as tmp:
            source = clone_upstream(args.repo_url, Path(tmp))
            result = sync_cookbook_assets(
                source_root=source,
                output_root=args.output_dir.resolve(),
                upstream_url=args.repo_url,
                commit_sha=git_commit_sha(source),
            )

    print(f"Synced {result['style_count']} styles from {result['commit_sha']} to {args.output_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run sync tests and full core tests**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add tests/test_cookbook_core.py skills/visual-prompt-cookbook/scripts/cookbook_core.py skills/visual-prompt-cookbook/scripts/sync_cookbook.py
git commit -m "feat: sync cookbook assets and build index"
```

## Task 3: Prompt CLI and Skill Metadata

**Files:**
- Create: `skills/visual-prompt-cookbook/scripts/render_prompt.py`
- Create: `skills/visual-prompt-cookbook/SKILL.md`
- Create: `skills/visual-prompt-cookbook/agents/openai.yaml`
- Create: `skills/visual-prompt-cookbook/references/usage-workflow.md`
- Modify: `tests/test_cookbook_core.py`

- [ ] **Step 1: Add failing CLI-oriented prompt render test**

Append to `PromptRenderTests` in `tests/test_cookbook_core.py`:

```python
    def test_find_style_by_id_or_slug(self) -> None:
        index = {
            "styles": [
                {"id": 1, "style_slug": "mono-test-poster", "style_name": "Mono Test Poster"},
                {"id": 2, "style_slug": "bright-ad", "style_name": "Bright Ad"},
            ]
        }
        self.assertEqual(core.find_style(index, "1")["style_slug"], "mono-test-poster")
        self.assertEqual(core.find_style(index, "bright-ad")["id"], 2)
        self.assertEqual(core.find_style(index, "bright")["id"], 2)
        with self.assertRaisesRegex(ValueError, "No style matched"):
            core.find_style(index, "missing")
```

- [ ] **Step 2: Run test and verify it fails because `find_style` is missing**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core.PromptRenderTests.test_find_style_by_id_or_slug -v
```

Expected: fail with `AttributeError` for `find_style`.

- [ ] **Step 3: Implement style lookup helper and prompt CLI**

Append to `cookbook_core.py`:

```python
def find_style(index: dict[str, Any], query: str) -> dict[str, Any]:
    normalized = query.strip().lower()
    for entry in index.get("styles", []):
        if str(entry.get("id")) == normalized:
            return entry
    matches = [
        entry
        for entry in index.get("styles", [])
        if normalized in entry.get("style_slug", "").lower()
        or normalized in entry.get("style_name", "").lower()
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(f"{entry['id']}:{entry['style_slug']}" for entry in matches[:8])
        raise ValueError(f"Multiple styles matched {query!r}: {names}")
    raise ValueError(f"No style matched {query!r}")
```

Create `skills/visual-prompt-cookbook/scripts/render_prompt.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cookbook_core import default_cookbook_root, find_style, read_json, render_prompt


def load_values(args: argparse.Namespace) -> dict[str, str]:
    if args.values_json:
        return read_json(args.values_json)
    if args.values:
        return json.loads(args.values)
    raise SystemExit("Provide --values-json or --values")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a final prompt from a Cookbook style.")
    parser.add_argument("style", help="Style id, slug, name fragment, or path to style.json")
    parser.add_argument("--cookbook-root", type=Path, default=default_cookbook_root())
    parser.add_argument("--values-json", type=Path)
    parser.add_argument("--values", help="Inline JSON object with variable values.")
    parser.add_argument("--json", action="store_true", help="Emit JSON with prompt and metadata.")
    args = parser.parse_args()

    style_arg = Path(args.style)
    if style_arg.exists():
        style_path = style_arg
        style = read_json(style_path)
        entry = {"style_slug": style["style_slug"], "style_name": style["style_name"], "id": None}
    else:
        index = read_json(args.cookbook_root / "styles-index.json")
        entry = find_style(index, args.style)
        style_path = args.cookbook_root / "styles" / entry["style_slug"] / "style.json"
        style = read_json(style_path)

    prompt = render_prompt(style, load_values(args))
    if args.json:
        print(json.dumps({"style": entry, "prompt": prompt}, ensure_ascii=False, indent=2))
    else:
        print(prompt)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create skill metadata and workflow reference**

Create `skills/visual-prompt-cookbook/SKILL.md`:

```markdown
---
name: visual-prompt-cookbook
description: Use when the user wants to create refined AI images, visual prompts, posters, ads, covers, social visuals, or reuse AI Visual Prompt Cookbook styles; helps browse styles in a local dashboard, select a style, infer variables, render final prompts, and optionally hand off to image generation when explicitly requested.
---

# Visual Prompt Cookbook

Use this skill to turn AI Visual Prompt Cookbook styles into usable image prompts.

## Workflow

1. If the user has not chosen a style, run:
   ```bash
   uv run python skills/visual-prompt-cookbook/scripts/serve_dashboard.py
   ```
   Open the printed local URL. Tell the user they can click a style in the dashboard or reply with an id, slug, or name.
2. Read `assets/cookbook/styles-index.json` to resolve the selected style. If needed, use:
   ```bash
   uv run python skills/visual-prompt-cookbook/scripts/render_prompt.py <style> --values-json /path/to/values.json
   ```
3. Read only the selected `style.json`, not the whole style library.
4. Infer a complete variable draft from the user's request. Prefer proactive completion over asking follow-up questions.
5. In the reply, show the selected style, variable draft, which values were inferred, and the final prompt.
6. Default to prompt output. If the user explicitly asks to generate the image, use the existing image generation workflow with the rendered prompt.

## Variable Drafting Rules

- Treat `environment_variables` as the contract for variables the user can edit.
- Fill missing values with tasteful, context-aware inferred values.
- Mark inferred values clearly.
- Keep exact user-provided text when the user supplies headline or copy.
- Preserve the style's `style_fidelity_anchors`, `source_content_to_avoid`, and `negative_prompt`.

For longer guidance, read `references/usage-workflow.md`.
```

Create `skills/visual-prompt-cookbook/agents/openai.yaml`:

```yaml
interface:
  display_name: "Visual Prompt Cookbook"
  short_description: "Browse visual styles and render polished image prompts."
  brand_color: "#111827"
  default_prompt: "Use $visual-prompt-cookbook to help me choose a refined visual style and draft a final image prompt."

policy:
  allow_implicit_invocation: true
```

Create `skills/visual-prompt-cookbook/references/usage-workflow.md`:

```markdown
# Usage Workflow

## Style Selection

Use the dashboard when the user needs to browse options visually. If the user already provides an id, slug, or style name, skip the dashboard and resolve the style directly from `assets/cookbook/styles-index.json`.

## Variable Draft

Return a compact table with:

- variable name
- value
- source: `user` or `inferred`
- short reason

If the user supplies minimal input, generate a complete first draft instead of blocking on questions. Ask a follow-up only when the request is unsafe, contradictory, or impossible to render.

## Final Prompt

Render the selected `prompt_template` with the final variables. Do not leave `{VARIABLE}` placeholders in the final prompt. Include the negative prompt when the selected style requires it.

## Image Generation

Only generate an image when the user explicitly asks for generation. Otherwise, stop after the final prompt.
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add tests/test_cookbook_core.py skills/visual-prompt-cookbook/scripts/cookbook_core.py skills/visual-prompt-cookbook/scripts/render_prompt.py skills/visual-prompt-cookbook/SKILL.md skills/visual-prompt-cookbook/agents/openai.yaml skills/visual-prompt-cookbook/references/usage-workflow.md
git commit -m "feat: add prompt rendering skill workflow"
```

## Task 4: Dashboard Server and Static UI

**Files:**
- Modify: `skills/visual-prompt-cookbook/scripts/cookbook_core.py`
- Create: `skills/visual-prompt-cookbook/scripts/serve_dashboard.py`
- Create: `skills/visual-prompt-cookbook/assets/dashboard/index.html`
- Create: `skills/visual-prompt-cookbook/assets/dashboard/app.js`
- Create: `skills/visual-prompt-cookbook/assets/dashboard/styles.css`
- Create: `tests/test_dashboard_server.py`

- [ ] **Step 1: Write failing dashboard helper tests**

Create `tests/test_dashboard_server.py`:

```python
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
```

- [ ] **Step 2: Run dashboard tests and verify missing helpers fail**

Run:

```bash
uv run python -m unittest tests.test_dashboard_server -v
```

Expected: fail with `AttributeError` for `record_dashboard_selection`.

- [ ] **Step 3: Implement dashboard helpers and server**

Append to `cookbook_core.py`:

```python
def dashboard_paths(skill_root: Path | None = None) -> dict[str, Path]:
    root = skill_root or default_skill_root()
    return {
        "dashboard_root": root / "assets" / "dashboard",
        "cookbook_root": root / "assets" / "cookbook",
        "state_dir": root / ".dashboard-state",
    }


def record_dashboard_selection(state_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    event = {"type": "style_selected", "timestamp": utc_now_iso(), **payload}
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event
```

Create `skills/visual-prompt-cookbook/scripts/serve_dashboard.py`:

```python
from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from cookbook_core import dashboard_paths, record_dashboard_selection


class DashboardHandler(SimpleHTTPRequestHandler):
    dashboard_root: Path
    cookbook_root: Path
    state_dir: Path

    def translate_path(self, path: str) -> str:
        clean = unquote(path.split("?", 1)[0].split("#", 1)[0])
        if clean in ("", "/"):
            return str(self.dashboard_root / "index.html")
        if clean.startswith("/cookbook/"):
            return str(self.cookbook_root / clean.removeprefix("/cookbook/"))
        return str(self.dashboard_root / clean.lstrip("/"))

    def do_GET(self) -> None:
        if self.path == "/api/index":
            self._send_json(json.loads((self.cookbook_root / "styles-index.json").read_text(encoding="utf-8")))
            return
        if self.path.startswith("/api/style/"):
            slug = unquote(self.path.removeprefix("/api/style/"))
            self._send_json(json.loads((self.cookbook_root / "styles" / slug / "style.json").read_text(encoding="utf-8")))
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/select":
            self.send_error(404)
            return
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        event = record_dashboard_selection(self.state_dir, payload)
        self._send_json(event)

    def _send_json(self, payload: object) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Visual Prompt Cookbook dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    paths = dashboard_paths(args.skill_root.resolve())
    handler = type(
        "ConfiguredDashboardHandler",
        (DashboardHandler,),
        {
            "dashboard_root": paths["dashboard_root"],
            "cookbook_root": paths["cookbook_root"],
            "state_dir": paths["state_dir"],
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{server.server_port}"
    print(url, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create static dashboard assets**

Create `skills/visual-prompt-cookbook/assets/dashboard/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Visual Prompt Cookbook</title>
    <link rel="stylesheet" href="/styles.css">
  </head>
  <body>
    <header class="topbar">
      <div>
        <h1>Visual Prompt Cookbook</h1>
        <p id="meta">Loading styles...</p>
      </div>
      <input id="search" type="search" placeholder="Search styles, tags, or slug">
    </header>
    <main>
      <section id="grid" class="grid" aria-label="Style gallery"></section>
      <aside id="detail" class="detail" aria-label="Style detail">
        <p class="muted">Select a style to inspect variables and examples.</p>
      </aside>
    </main>
    <script src="/app.js"></script>
  </body>
</html>
```

Create `skills/visual-prompt-cookbook/assets/dashboard/app.js`:

```javascript
let styles = [];

const grid = document.querySelector("#grid");
const detail = document.querySelector("#detail");
const search = document.querySelector("#search");
const meta = document.querySelector("#meta");

function matchStyle(style, query) {
  const haystack = [
    style.id,
    style.style_name,
    style.style_slug,
    style.style_summary,
    ...(style.tags || []),
  ].join(" ").toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function card(style) {
  const node = document.createElement("button");
  node.className = "card";
  node.type = "button";
  node.innerHTML = `
    <img src="/cookbook/${style.preview_16x9}" alt="">
    <span class="id">#${style.id}</span>
    <h2>${style.style_name}</h2>
    <p>${style.style_summary}</p>
    <small>${(style.tags || []).join(" / ")}</small>
  `;
  node.addEventListener("click", () => selectStyle(style));
  return node;
}

function renderGrid() {
  const query = search.value.trim();
  grid.innerHTML = "";
  styles.filter((style) => !query || matchStyle(style, query)).forEach((style) => grid.appendChild(card(style)));
}

async function selectStyle(style) {
  const response = await fetch(`/api/style/${style.style_slug}`);
  const data = await response.json();
  await fetch("/api/select", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ id: style.id, style_slug: style.style_slug, style_name: style.style_name }),
  });
  detail.innerHTML = `
    <img class="hero" src="/cookbook/${style.preview_9x16}" alt="">
    <h2>#${style.id} ${style.style_name}</h2>
    <p>${style.style_summary}</p>
    <h3>Variables</h3>
    <dl>
      ${Object.entries(data.environment_variables || {}).map(([name, desc]) => `<dt>${name}</dt><dd>${desc}</dd>`).join("")}
    </dl>
    <p class="muted">Reply in Codex with #${style.id} or ${style.style_slug} to continue.</p>
  `;
}

async function init() {
  const response = await fetch("/api/index");
  const index = await response.json();
  styles = index.styles || [];
  meta.textContent = `${index.style_count || styles.length} styles · upstream ${index.upstream?.commit_sha || "unknown"}`;
  renderGrid();
}

search.addEventListener("input", renderGrid);
init().catch((error) => {
  meta.textContent = `Failed to load styles: ${error}`;
});
```

Create `skills/visual-prompt-cookbook/assets/dashboard/styles.css`:

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #151515;
  background: #f6f5f1;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid #ddd7cb;
  background: rgba(246, 245, 241, 0.96);
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 4px;
  font-size: 24px;
}

#search {
  width: min(420px, 42vw);
  padding: 10px 12px;
  border: 1px solid #c9c2b6;
  border-radius: 6px;
  background: #fff;
  font-size: 15px;
}

main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 20px;
  padding: 20px 24px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.card {
  min-height: 330px;
  padding: 0 0 14px;
  overflow: hidden;
  text-align: left;
  border: 1px solid #ddd7cb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.card:hover {
  border-color: #111;
}

.card img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.card h2,
.card p,
.card small,
.card .id {
  display: block;
  margin-right: 14px;
  margin-left: 14px;
}

.card .id {
  margin-top: 12px;
  color: #6b5f50;
  font-size: 12px;
}

.card h2 {
  margin-bottom: 8px;
  font-size: 18px;
}

.card p {
  color: #423c33;
  line-height: 1.45;
}

.detail {
  position: sticky;
  top: 96px;
  align-self: start;
  max-height: calc(100vh - 120px);
  overflow: auto;
  padding: 16px;
  border: 1px solid #ddd7cb;
  border-radius: 8px;
  background: #fff;
}

.detail .hero {
  width: 100%;
  border-radius: 6px;
}

dt {
  margin-top: 12px;
  font-weight: 700;
}

dd {
  margin-left: 0;
  color: #423c33;
}

.muted {
  color: #6b5f50;
}

@media (max-width: 900px) {
  .topbar,
  main {
    display: block;
  }

  #search {
    width: 100%;
    margin-top: 14px;
  }

  .detail {
    position: static;
    margin-top: 18px;
    max-height: none;
  }
}
```

- [ ] **Step 5: Run dashboard tests and all tests**

Run:

```bash
uv run python -m unittest tests.test_dashboard_server tests.test_cookbook_core -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add tests/test_dashboard_server.py skills/visual-prompt-cookbook/scripts/cookbook_core.py skills/visual-prompt-cookbook/scripts/serve_dashboard.py skills/visual-prompt-cookbook/assets/dashboard/index.html skills/visual-prompt-cookbook/assets/dashboard/app.js skills/visual-prompt-cookbook/assets/dashboard/styles.css
git commit -m "feat: add visual prompt dashboard"
```

## Task 5: Install Helper, Real Sync, and Verification

**Files:**
- Modify: `skills/visual-prompt-cookbook/scripts/cookbook_core.py`
- Create: `skills/visual-prompt-cookbook/scripts/install_skill.py`
- Modify: `tests/test_cookbook_core.py`
- Generated by sync: `skills/visual-prompt-cookbook/assets/cookbook/**`

- [ ] **Step 1: Add failing install helper test**

Append to `tests/test_cookbook_core.py`:

```python
class InstallSkillTests(unittest.TestCase):
    def test_install_skill_copies_tree_and_skips_dashboard_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "skill"
            target_root = Path(tmp) / "skills"
            (source / "scripts").mkdir(parents=True)
            (source / "scripts" / "tool.py").write_text("print('ok')", encoding="utf-8")
            (source / ".dashboard-state").mkdir()
            (source / ".dashboard-state" / "events.jsonl").write_text("{}", encoding="utf-8")

            installed = core.install_skill_tree(source, target_root)

            self.assertEqual(installed, target_root / "visual-prompt-cookbook")
            self.assertTrue((installed / "scripts" / "tool.py").exists())
            self.assertFalse((installed / ".dashboard-state").exists())
```

- [ ] **Step 2: Run install test and verify helper is missing**

Run:

```bash
uv run python -m unittest tests.test_cookbook_core.InstallSkillTests -v
```

Expected: fail with `AttributeError` for `install_skill_tree`.

- [ ] **Step 3: Implement install helper and CLI**

Append to `cookbook_core.py`:

```python
def install_skill_tree(source_root: Path, skills_root: Path) -> Path:
    target = skills_root / "visual-prompt-cookbook"
    if target.exists():
        shutil.rmtree(target)

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".dashboard-state", "__pycache__"} or name.endswith(".pyc")}

    shutil.copytree(source_root, target, ignore=ignore)
    return target
```

Create `skills/visual-prompt-cookbook/scripts/install_skill.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from cookbook_core import default_skill_root, install_skill_tree


def main() -> None:
    parser = argparse.ArgumentParser(description="Install visual-prompt-cookbook into local Codex skills.")
    parser.add_argument("--source-root", type=Path, default=default_skill_root())
    parser.add_argument("--skills-root", type=Path, default=Path.home() / ".codex" / "skills")
    args = parser.parse_args()

    target = install_skill_tree(args.source_root.resolve(), args.skills_root.expanduser().resolve())
    print(f"Installed visual-prompt-cookbook to {target}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all automated tests**

Run:

```bash
uv run python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Sync real upstream Cookbook assets**

Run:

```bash
uv run python skills/visual-prompt-cookbook/scripts/sync_cookbook.py
```

Expected: prints `Synced 56 styles ...` or a newer count if upstream changed.

- [ ] **Step 6: Verify prompt rendering on a real synced style**

Run:

```bash
uv run python skills/visual-prompt-cookbook/scripts/render_prompt.py mono-noir-type-portrait-poster-style --values '{"SUBJECT":"a tired architect with silver hair","SUBJECT_ACTION":"studying a folded blueprint","PRODUCT_OR_PROP":"a rolled plan tube","LOCATION":"a dim concrete studio","BACKGROUND_ELEMENTS":"soft charcoal wall gradient","MAIN_TEXT":"focus / outlasts / noise.","SECONDARY_TEXT":"studio log 02:14","ACCENT_SYMBOL":"a tiny white plus","WARDROBE_STYLE":"dark work jacket over a plain black shirt","ASPECT_RATIO":"16:9"}' | head -5
```

Expected: prompt starts with the selected style wording and contains no raw `{VARIABLE}` placeholders.

- [ ] **Step 7: Install the skill**

Run:

```bash
uv run python skills/visual-prompt-cookbook/scripts/install_skill.py
```

Expected: prints installed path under `~/.codex/skills/visual-prompt-cookbook`.

- [ ] **Step 8: Smoke test dashboard server**

Run:

```bash
uv run python skills/visual-prompt-cookbook/scripts/serve_dashboard.py --port 8765
```

Expected: prints `http://127.0.0.1:8765`. Open this URL in the in-app browser and verify the dashboard shows style cards and preview images. Stop the server after verification.

- [ ] **Step 9: Commit Task 5 and generated synced assets**

Run:

```bash
git add tests/test_cookbook_core.py skills/visual-prompt-cookbook/scripts/cookbook_core.py skills/visual-prompt-cookbook/scripts/install_skill.py skills/visual-prompt-cookbook/assets/cookbook
git commit -m "feat: install and sync visual prompt skill"
```

## Self-Review

- Spec coverage: Tasks cover source repo structure, refreshable upstream sync, index generation, dashboard, proactive prompt rendering workflow, installation, and verification.
- Placeholder scan: This plan contains no unresolved placeholder markers or unfinished file names.
- Type consistency: Shared helpers are defined in `cookbook_core.py`; CLI scripts import those helpers by sibling module import, which works both in the source repo and installed skill.
- Execution choice: Because the user already requested implementation and subagent spawning requires explicit user permission in this environment, execute this plan inline using `superpowers:executing-plans`.
