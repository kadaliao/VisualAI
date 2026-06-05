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
