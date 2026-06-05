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
