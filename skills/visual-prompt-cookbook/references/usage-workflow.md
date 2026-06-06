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

Only generate an image when the user explicitly asks for generation and the current agent clearly has an image generation tool. Otherwise, stop after the final prompt.

Do not ask whether to generate an image unless the current agent can actually do it. If no image generation tool is available, deliver the prompt and variables without offering generation as a next step. If the user asks for generation in a tool-less agent, state that this agent can prepare the prompt but cannot render the image here.
