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
