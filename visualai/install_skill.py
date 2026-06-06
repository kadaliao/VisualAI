from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


SKILL_NAME = "visual-prompt-cookbook"
SKILL_RELATIVE_PATH = Path("skills") / SKILL_NAME
DEFAULT_ARCHIVE_URL = "https://github.com/kadaliao/VisualAI/archive/refs/heads/main.zip"


def default_local_skill_root() -> Path:
    return Path(__file__).resolve().parents[1] / SKILL_RELATIVE_PATH


def assert_skill_root(path: Path) -> Path:
    if not (path / "SKILL.md").is_file():
        raise FileNotFoundError(f"Missing Codex skill at {path}")
    return path


def find_archived_skill_root(extract_root: Path) -> Path:
    for skill_file in extract_root.rglob("SKILL.md"):
        skill_root = skill_file.parent
        if skill_root.name == SKILL_NAME and skill_root.parent.name == "skills":
            return skill_root
    raise FileNotFoundError(f"Archive does not contain {SKILL_RELATIVE_PATH}")


def download_skill_root(archive_url: str, work_dir: Path) -> Path:
    archive_path = work_dir / "visualai.zip"
    urllib.request.urlretrieve(archive_url, archive_path)
    extract_root = work_dir / "archive"
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_root)
    return find_archived_skill_root(extract_root)


def install_skill_tree(source_root: Path, skills_root: Path) -> Path:
    source_root = assert_skill_root(source_root)
    target = skills_root / SKILL_NAME
    if target.exists():
        shutil.rmtree(target)

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".dashboard-state", "__pycache__"} or name.endswith(".pyc")}

    shutil.copytree(source_root, target, ignore=ignore)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Install visual-prompt-cookbook into local Codex skills.")
    parser.add_argument("--source-root", type=Path, help="Install from a local skill directory.")
    parser.add_argument(
        "--archive-url",
        help=(
            "Install from a VisualAI source archive. If omitted, the installer uses the local "
            f"checkout when available, otherwise downloads {DEFAULT_ARCHIVE_URL}."
        ),
    )
    parser.add_argument("--skills-root", type=Path, default=Path.home() / ".codex" / "skills")
    args = parser.parse_args()

    if args.source_root and args.archive_url:
        parser.error("--source-root and --archive-url cannot be used together")

    skills_root = args.skills_root.expanduser().resolve()
    if args.source_root:
        target = install_skill_tree(args.source_root.expanduser().resolve(), skills_root)
    elif args.archive_url:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = download_skill_root(args.archive_url, Path(tmp))
            target = install_skill_tree(source_root, skills_root)
    else:
        local_source = default_local_skill_root()
        if (local_source / "SKILL.md").is_file():
            target = install_skill_tree(local_source.resolve(), skills_root)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                source_root = download_skill_root(DEFAULT_ARCHIVE_URL, Path(tmp))
                target = install_skill_tree(source_root, skills_root)

    print(f"Installed visual-prompt-cookbook to {target}")


if __name__ == "__main__":
    main()
