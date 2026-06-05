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
