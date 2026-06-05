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
