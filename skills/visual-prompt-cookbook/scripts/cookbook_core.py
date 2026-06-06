from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from string import Formatter
from typing import Any


SPECIAL_TEMPLATE_VALUES = {
    "STYLE_FIDELITY_ANCHORS": "style_fidelity_anchors",
    "SOURCE_CONTENT_TO_AVOID": "source_content_to_avoid",
    "NEGATIVE_PROMPT": "negative_prompt",
}

DASHBOARD_LANGUAGES = {"auto", "en", "zh-CN"}
DASHBOARD_ZH_FALLBACK_SUMMARY = (
    "来自 upstream 的新风格。当前还没有人工中文摘要；可先通过预览图判断视觉方向，"
    "选择后当前 agent 会读取原始风格定义并生成可用提示词。"
)
DASHBOARD_ZH_TAGS = {
    "poster": "海报",
    "fashion": "时尚",
    "product": "产品",
    "collage": "拼贴",
    "photo": "摄影",
    "typography": "文字",
    "travel": "旅行",
    "food": "食物",
    "visual": "视觉",
}
DASHBOARD_ZH_VARIABLES = {
    "SUBJECT": {
        "label": "主体",
        "description": "画面主角或核心对象，例如人物、角色、产品、宠物、建筑、食物或场景中的主要视觉锚点。",
    },
    "SUBJECT_ACTION": {
        "label": "主体动作",
        "description": "主体正在做的事或姿态，例如看向镜头、奔跑、展示产品、摆姿势、互动或停在某个瞬间。",
    },
    "PRODUCT_OR_PROP": {
        "label": "产品或道具",
        "description": "需要出现的产品、道具、配件或辅助物件，用来强化主题、用途或故事线索。",
    },
    "LOCATION": {
        "label": "场景地点",
        "description": "画面发生的位置或空间类型，例如室内、街头、交通工具、展览空间、自然环境或具体城市地点。",
    },
    "BACKGROUND_ELEMENTS": {
        "label": "背景元素",
        "description": "背景里的纹理、陈列、标识、天气、装饰、辅助人物或其他能丰富画面层次的细节。",
    },
    "MAIN_TEXT": {
        "label": "主标题",
        "description": "画面中最醒目的短文字，适合使用 1 到 6 个词或很短的中文短句。",
    },
    "SECONDARY_TEXT": {
        "label": "辅助文字",
        "description": "小字号说明、标签、日期、路线注释、广告副文案或作为视觉肌理的微文案。",
    },
    "ACCENT_SYMBOL": {
        "label": "点缀符号",
        "description": "强化风格的装饰元素，例如箭头、星形、贴纸、速度线、手绘圈、徽章、闪电或符号标记。",
    },
    "WARDROBE_STYLE": {
        "label": "服装造型",
        "description": "人物、角色或主体的穿搭、材质、配色、表情、表面处理或整体造型方向。",
    },
    "ASPECT_RATIO": {
        "label": "画幅比例",
        "description": "最终图片比例，例如 9:16 竖图、16:9 横图、1:1 方图或其他生成工具支持的比例。",
    },
    "STYLE_FIDELITY_ANCHORS": {
        "label": "风格锚点",
        "description": "必须保留的视觉特征，用来确保换主题后仍然像同一个风格系统。",
    },
    "SOURCE_CONTENT_TO_AVOID": {
        "label": "需避开的源内容",
        "description": "不能复刻或误用的来源元素，例如真实品牌、人物、水印、平台标识、二维码或原图专属细节。",
    },
    "NEGATIVE_PROMPT": {
        "label": "负面提示词",
        "description": "生成时需要排除的画面风格、元素、质量问题或版权风险内容。",
    },
    "CHARACTER_DIFFERENCE_RULE": {
        "label": "角色差异规则",
        "description": "同一画面中不同角色的区分方式，例如年龄、服装、体型、表情、颜色或轮廓差异。",
    },
    "DELIVERY_FORMAT": {
        "label": "交付形式",
        "description": "最终图片的呈现形态，例如单张海报、长图、横版封面、社媒图或系列模板。",
    },
    "DOODLE_COMPANION": {
        "label": "涂鸦伙伴",
        "description": "陪伴主体的小角色、贴纸、幻想动物、玩偶、吉祥物或手绘叙事元素。",
    },
    "DOODLE_SCALE": {
        "label": "涂鸦比例",
        "description": "涂鸦元素相对真实主体或场景的大小关系，例如巨大覆盖、局部点缀或小比例陪伴。",
    },
    "LENS_STYLE": {
        "label": "镜头风格",
        "description": "画面的镜头语言，例如鱼眼、广角、微距、低机位、手机快照、棚拍或纪实摄影质感。",
    },
    "LIGHT_SOURCE": {
        "label": "光源",
        "description": "主光和氛围光来源，例如阳光、屏幕光、霓虹、闪光灯、棚灯、车窗光或环境反射。",
    },
    "PRIMARY_COLOR": {
        "label": "主色",
        "description": "画面中占主导地位的颜色，用来控制整体气质和识别度。",
    },
    "SECONDARY_COLOR": {
        "label": "辅助色",
        "description": "配合主色使用的第二颜色，用来制造对比、层次或局部强调。",
    },
    "PRODUCT_CATEGORY": {
        "label": "产品类别",
        "description": "产品所属类型，例如饮料、科技设备、玩具、家具、服饰、食品或生活方式用品。",
    },
    "PRODUCT_TEXTURE": {
        "label": "产品质感",
        "description": "产品表面的材料和触感，例如毛绒、金属、玻璃、塑料、纸张、织物、磨砂或高光。",
    },
    "SUBJECT_IDENTITY": {
        "label": "主体身份",
        "description": "主体的身份设定，例如创作者、游客、运动员、学生、模特、厨师、驾驶者或品牌角色。",
    },
    "TEXTURE_LEVEL": {
        "label": "纹理强度",
        "description": "纸张、颗粒、扫描感、噪点、油墨、磨损或手工痕迹的强弱程度。",
    },
    "TYPOGRAPHY_LANGUAGE": {
        "label": "文字语言",
        "description": "画面文字使用的语言或混排方式，例如中文、英文、双语、日文风格字形或短标签混排。",
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_dashboard_locale(language: str | None, skill_root: Path | None = None) -> dict[str, Any]:
    normalized = normalize_dashboard_language(language)
    if normalized == "auto":
        return {}
    locale_path = (skill_root or default_skill_root()) / "assets" / "dashboard" / "locales" / f"{normalized}.json"
    if not locale_path.exists():
        return {}
    data = read_json(locale_path)
    return data if isinstance(data, dict) else {}


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


def dashboard_paths(skill_root: Path | None = None) -> dict[str, Path]:
    root = skill_root or default_skill_root()
    return {
        "dashboard_root": root / "assets" / "dashboard",
        "cookbook_root": root / "assets" / "cookbook",
        "state_dir": root / ".dashboard-state",
    }


def normalize_dashboard_language(language: str | None) -> str:
    if not language:
        return "auto"
    normalized = language.strip().replace("_", "-").lower()
    if not normalized or normalized == "auto":
        return "auto"
    if normalized.startswith("zh"):
        return "zh-CN"
    if normalized.startswith("en"):
        return "en"
    return "auto"


def _dashboard_locale_with_defaults(locale: dict[str, Any] | None) -> dict[str, Any]:
    merged = {
        "styles": {},
        "tags": DASHBOARD_ZH_TAGS,
        "variables": DASHBOARD_ZH_VARIABLES,
    }
    if not locale:
        return merged
    if isinstance(locale.get("styles"), dict):
        merged["styles"] = locale["styles"]
    if isinstance(locale.get("tags"), dict):
        merged["tags"] = {**DASHBOARD_ZH_TAGS, **locale["tags"]}
    if isinstance(locale.get("variables"), dict):
        merged["variables"] = {**DASHBOARD_ZH_VARIABLES, **locale["variables"]}
    return merged


def _dashboard_fallback_style_name(style: dict[str, Any]) -> str:
    style_id = style.get("id")
    if style_id:
        return f"视觉风格 #{style_id}"
    slug = style.get("style_slug")
    return f"视觉风格：{slug}" if slug else "视觉风格"


def _dashboard_variable_display(name: str, locale: dict[str, Any]) -> dict[str, str]:
    translated = locale["variables"].get(name, {})
    label = translated.get("label") or name.replace("_", " ").title()
    description = translated.get("description") or f"根据画面需求填写“{label}”。"
    return {"label": label, "description": description}


def _dashboard_display(style: dict[str, Any], locale: dict[str, Any]) -> dict[str, Any]:
    style_locale = locale["styles"].get(style.get("style_slug", ""), {})
    display: dict[str, Any] = {
        "name": style_locale.get("name") or _dashboard_fallback_style_name(style),
        "summary": style_locale.get("summary") or DASHBOARD_ZH_FALLBACK_SUMMARY,
        "tags": [locale["tags"].get(tag, tag) for tag in style.get("tags", [])],
    }
    variables = style.get("environment_variables")
    if isinstance(variables, dict):
        display["environment_variables"] = {
            name: _dashboard_variable_display(name, locale) for name in variables.keys()
        }
    return display


def localize_dashboard_style(
    style: dict[str, Any],
    language: str | None,
    locale: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = deepcopy(style)
    if normalize_dashboard_language(language) != "zh-CN":
        return payload
    payload["display"] = _dashboard_display(payload, _dashboard_locale_with_defaults(locale))
    return payload


def localize_dashboard_index(
    index: dict[str, Any],
    language: str | None,
    locale: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = deepcopy(index)
    if normalize_dashboard_language(language) != "zh-CN":
        return payload
    locale_with_defaults = _dashboard_locale_with_defaults(locale)
    payload["styles"] = [
        {**entry, "display": _dashboard_display(entry, locale_with_defaults)}
        for entry in payload.get("styles", [])
    ]
    return payload


def record_dashboard_selection(state_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    event = {"type": "style_selected", "timestamp": utc_now_iso(), **payload}
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def install_skill_tree(source_root: Path, skills_root: Path) -> Path:
    target = skills_root / "visual-prompt-cookbook"
    if target.exists():
        shutil.rmtree(target)

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".dashboard-state", "__pycache__"} or name.endswith(".pyc")}

    shutil.copytree(source_root, target, ignore=ignore)
    return target
