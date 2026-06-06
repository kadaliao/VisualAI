---
name: visual-prompt-cookbook
description: Use when the user wants to make, draw, generate, or design an image; asks in Chinese for 作图、画图、出图、做图、海报、封面、配图、广告图、社媒图、视觉稿、图片提示词; wants refined AI image prompts, posters, ads, covers, social visuals, or reuse AI Visual Prompt Cookbook styles. Helps browse styles in a local dashboard, select a style, collect the subject/content brief, infer variables, render final prompts, and optionally hand off to image generation when explicitly requested.
---

# Visual Prompt Cookbook

Use this skill to turn AI Visual Prompt Cookbook styles into usable image prompts.

## Workflow

1. If the user has not chosen a style, run:
   ```bash
   uv run python skills/visual-prompt-cookbook/scripts/serve_dashboard.py --language <conversation-language>
   ```
   Use the user's current conversation language, for example `--language zh-CN` for Chinese or `--language en` for English. This command starts the dashboard in the background, prints the local URL, and opens the browser. Do not run the foreground server unless you need to debug it. Tell the user they can click a style in the dashboard or reply with an id, slug, or name.
2. When the user chooses a style by id, slug, name, or dashboard click, read `assets/cookbook/styles-index.json` to resolve the selected style. If needed, use:
   ```bash
   uv run python skills/visual-prompt-cookbook/scripts/render_prompt.py <style> --values-json /path/to/values.json
   ```
3. Read only the selected `style.json`, not the whole style library.
4. After style selection, immediately continue the image-brief workflow. Do not stop at "style selected." Use the selected style's `environment_variables` as the variable contract, then either infer missing values from the conversation or ask one concise question for the core missing brief.
5. If the user has only provided a style number/name and no content brief, ask for the subject/theme and any required text/copy in the user's language. Mention only the most important fields for that style, such as subject, setting/use case, main text, mood, product/prop, and aspect ratio; do not ask the user to fill a raw variable table.
6. Infer a complete variable draft once enough brief exists. Prefer proactive completion over asking follow-up questions.
7. In the reply, show the selected style, variable draft, which values were inferred, and the final prompt.
8. Default to prompt output. Only generate an image when the user explicitly asks for generation and the current agent clearly has an image generation tool. If the current agent does not have image generation capability, stop after the prompt; do not ask whether to generate an image or offer generation as a next step.

## Variable Drafting Rules

- Treat `environment_variables` as the contract for variables the user can edit.
- Fill missing values with tasteful, context-aware inferred values.
- Mark inferred values clearly.
- Keep exact user-provided text when the user supplies headline or copy.
- Preserve the style's `style_fidelity_anchors`, `source_content_to_avoid`, and `negative_prompt`.

## Agent Capability Rule

- Do not ask whether to generate an image unless the current agent clearly has an image generation tool available.
- If no image generation tool is available, silently treat the deliverable as the rendered prompt plus variables.
- If the user explicitly asks this agent to generate an image but no generation tool exists, say that this agent can prepare the prompt but cannot render the image here.

For longer guidance, read `references/usage-workflow.md`.

## Upstream And Updates

The bundled styles come from `git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git`. The synced assets keep the upstream `LICENSE`, schema, commit SHA, and sync time in `assets/cookbook/`.

To refresh styles from upstream in the source repo, run:

```bash
uv run python skills/visual-prompt-cookbook/scripts/sync_cookbook.py
uv run visualai-install --agent <agent>
```
