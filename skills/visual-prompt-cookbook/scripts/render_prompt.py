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
