from __future__ import annotations

import argparse
import http.client
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


SKILL_NAME = "visual-prompt-cookbook"
SKILL_RELATIVE_PATH = Path("skills") / SKILL_NAME
DEFAULT_ARCHIVE_URL = "https://github.com/kadaliao/VisualAI/archive/refs/heads/main.zip"
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_ERRORS = (http.client.IncompleteRead, OSError, urllib.error.URLError)


@dataclass(frozen=True)
class AgentTarget:
    name: str
    label: str
    default_root: Path | None
    layout: str
    note: str


AGENTS: dict[str, AgentTarget] = {
    "codex": AgentTarget(
        name="codex",
        label="Codex",
        default_root=Path(".codex") / "skills",
        layout="skill",
        note="Installs to ~/.codex/skills.",
    ),
    "claude": AgentTarget(
        name="claude",
        label="Claude Code",
        default_root=Path(".claude") / "skills",
        layout="skill",
        note="Installs to ~/.claude/skills.",
    ),
    "cursor": AgentTarget(
        name="cursor",
        label="Cursor",
        default_root=Path(".cursor") / "skills",
        layout="skill",
        note="Installs to ~/.cursor/skills.",
    ),
    "gemini": AgentTarget(
        name="gemini",
        label="Gemini CLI",
        default_root=Path(".gemini") / "extensions",
        layout="gemini-extension",
        note="Installs as a Gemini extension under ~/.gemini/extensions.",
    ),
    "opencode": AgentTarget(
        name="opencode",
        label="OpenCode",
        default_root=Path(".config") / "opencode" / "skills",
        layout="skill",
        note="Installs to ~/.config/opencode/skills.",
    ),
    "windsurf": AgentTarget(
        name="windsurf",
        label="Windsurf",
        default_root=Path(".codeium") / "windsurf" / "skills",
        layout="skill",
        note="Installs to ~/.codeium/windsurf/skills.",
    ),
    "openclaw": AgentTarget(
        name="openclaw",
        label="OpenClaw",
        default_root=Path(".openclaw-autoclaw") / "skills",
        layout="skill",
        note="Installs to ~/.openclaw-autoclaw/skills.",
    ),
    "hermes": AgentTarget(
        name="hermes",
        label="Hermes Agent",
        default_root=Path(".hermes") / "skills",
        layout="skill",
        note="Installs to ~/.hermes/skills.",
    ),
    "custom": AgentTarget(
        name="custom",
        label="Custom directory",
        default_root=None,
        layout="skill",
        note="Installs to a directory passed with --target-root.",
    ),
}
INSTALL_ALL_AGENTS = ("codex", "claude", "cursor", "gemini", "opencode", "windsurf", "openclaw", "hermes")


def default_local_skill_root() -> Path:
    return Path(__file__).resolve().parents[1] / SKILL_RELATIVE_PATH


def assert_skill_root(path: Path) -> Path:
    if not (path / "SKILL.md").is_file():
        raise FileNotFoundError(f"Missing skill at {path}")
    return path


def find_archived_skill_root(extract_root: Path) -> Path:
    for skill_file in extract_root.rglob("SKILL.md"):
        skill_root = skill_file.parent
        if skill_root.name == SKILL_NAME and skill_root.parent.name == "skills":
            return skill_root
    raise FileNotFoundError(f"Archive does not contain {SKILL_RELATIVE_PATH}")


def format_bytes(size: int) -> str:
    units = ("B", "KB", "MB", "GB")
    value = float(max(size, 0))
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024


def download_progress_hook(*, enabled: bool):
    if not enabled:
        return None

    def report(block_count: int, block_size: int, total_size: int) -> None:
        downloaded = max(block_count * block_size, 0)
        if total_size > 0:
            downloaded = min(downloaded, total_size)
            percent = int(downloaded * 100 / total_size)
            filled = min(20, int(percent / 5))
            bar = "#" * filled + "-" * (20 - filled)
            sys.stdout.write(
                f"\rDownloading skill package [{bar}] {percent:3d}% "
                f"{format_bytes(downloaded)}/{format_bytes(total_size)}\033[K"
            )
        else:
            sys.stdout.write(
                f"\rDownloading skill package [{'?' * 20}] ---% "
                f"{format_bytes(downloaded)} downloaded\033[K"
            )
        sys.stdout.flush()

    return report


def download_skill_root(archive_url: str, work_dir: Path, *, verbose: bool = False) -> Path:
    archive_path = work_dir / "visualai.zip"
    if verbose:
        print("Downloading skill package...")
    last_error: BaseException | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            urllib.request.urlretrieve(archive_url, archive_path, reporthook=download_progress_hook(enabled=verbose))
            if verbose:
                print()
            break
        except DOWNLOAD_ERRORS as exc:
            last_error = exc
            archive_path.unlink(missing_ok=True)
            if verbose:
                print()
                if attempt < DOWNLOAD_ATTEMPTS:
                    print(f"Download interrupted; retrying ({attempt + 1}/{DOWNLOAD_ATTEMPTS})...")
    else:
        raise RuntimeError(f"Failed to download skill package after {DOWNLOAD_ATTEMPTS} attempts: {last_error}")

    extract_root = work_dir / "archive"
    if verbose:
        print("Unpacking skill package...")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
    except zipfile.BadZipFile as exc:
        raise RuntimeError("Downloaded archive is not a valid zip file; rerun the installer to download it again") from exc
    return find_archived_skill_root(extract_root)


def copy_skill_tree(source_root: Path, target: Path) -> Path:
    source_root = assert_skill_root(source_root)
    if target.exists():
        shutil.rmtree(target)

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".dashboard-state", "__pycache__"} or name.endswith(".pyc")}

    shutil.copytree(source_root, target, ignore=ignore)
    return target


def install_skill_tree(source_root: Path, skills_root: Path) -> Path:
    return copy_skill_tree(source_root, skills_root / SKILL_NAME)


def write_gemini_extension_manifest(extension_root: Path) -> None:
    manifest = {
        "name": SKILL_NAME,
        "version": "0.1.0",
        "description": "Visual prompt cookbook skill for generating image prompts.",
        "contextFileName": "GEMINI.md",
    }
    extension_root.mkdir(parents=True, exist_ok=True)
    (extension_root / "gemini-extension.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (extension_root / "GEMINI.md").write_text(
        "\n".join(
            [
                "# visual-prompt-cookbook",
                "",
                "Use the bundled skill at `skills/visual-prompt-cookbook/SKILL.md` for visual prompt workflows.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def install_for_agent(source_root: Path, target_root: Path, agent: AgentTarget) -> Path:
    if agent.layout == "gemini-extension":
        extension_root = target_root / SKILL_NAME
        if extension_root.exists():
            shutil.rmtree(extension_root)
        installed = copy_skill_tree(source_root, extension_root / "skills" / SKILL_NAME)
        write_gemini_extension_manifest(extension_root)
        return installed
    return install_skill_tree(source_root, target_root)


def resolve_target_root(agent: AgentTarget, home: Path, target_root: Path | None) -> Path:
    if target_root is not None:
        return target_root.expanduser().resolve()
    if agent.default_root is None:
        raise ValueError(f"--target-root is required for --agent {agent.name}")
    return (home / agent.default_root).expanduser().resolve()


def parse_agent(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "all" or normalized in AGENTS:
        return normalized
    valid = ", ".join([*AGENTS.keys(), "all"])
    raise argparse.ArgumentTypeError(f"unknown agent {value!r}; choose one of: {valid}")


def list_agents() -> str:
    lines = ["Available agents:"]
    for agent_name in INSTALL_ALL_AGENTS:
        agent = AGENTS[agent_name]
        lines.append(f"  {agent.name:<9} {agent.label:<18} {agent_destination(agent)}")
    lines.append("  all       All built-in agents  every built-in target")
    lines.append(f"  custom    {AGENTS['custom'].label:<18} pass --target-root or choose a path")
    return "\n".join(lines)


def agent_destination(agent: AgentTarget) -> str:
    if agent.default_root is None:
        return "custom path"
    return f"~/{agent.default_root.as_posix()}"


def interactive_choices() -> list[str]:
    return [*INSTALL_ALL_AGENTS, "all", "custom"]


def interactive_choice_label(choice: str) -> str:
    if choice == "all":
        return "All built-in agents"
    return AGENTS[choice].label


def interactive_choice_destination(choice: str) -> str:
    if choice == "all":
        return "every built-in target"
    if choice == "custom":
        return "enter a custom skill directory"
    return agent_destination(AGENTS[choice])


def choose_agent_interactively() -> str:
    choices = interactive_choices()
    print()
    print(f"Install {SKILL_NAME}")
    print()
    print("Choose an agent:")
    for index, choice in enumerate(choices, start=1):
        print(f"  {index:>2}. {interactive_choice_label(choice):<22} {interactive_choice_destination(choice)}")
    print()
    while True:
        try:
            selected = input("Enter number or agent name [1]:\n> ").strip().lower() or "1"
        except EOFError:
            return "codex"

        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(choices):
                return choices[index - 1]
        elif selected in choices:
            return selected

        print(f"Unknown choice {selected!r}.")


def prompt_target_root_interactively() -> Path:
    while True:
        try:
            selected = input("Custom skill directory:\n> ").strip()
        except EOFError as exc:
            raise ValueError("--target-root is required for --agent custom") from exc
        if selected:
            return Path(selected)
        print("Enter a directory path.")


def resolve_source_root(
    source_root: Path | None,
    archive_url: str | None,
    *,
    verbose: bool = False,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if source_root and archive_url:
        raise ValueError("--source-root and --archive-url cannot be used together")
    if source_root:
        return assert_skill_root(source_root.expanduser().resolve()), None
    if archive_url:
        tmp = tempfile.TemporaryDirectory()
        return download_skill_root(archive_url, Path(tmp.name), verbose=verbose), tmp

    local_source = default_local_skill_root()
    if (local_source / "SKILL.md").is_file():
        return assert_skill_root(local_source.resolve()), None

    tmp = tempfile.TemporaryDirectory()
    return download_skill_root(DEFAULT_ARCHIVE_URL, Path(tmp.name), verbose=verbose), tmp


def install_selected_agents(
    *,
    selected_agent: str,
    source_root: Path,
    home: Path,
    target_root: Path | None,
) -> list[tuple[AgentTarget, Path]]:
    agent_names = INSTALL_ALL_AGENTS if selected_agent == "all" else (selected_agent,)
    results: list[tuple[AgentTarget, Path]] = []
    for agent_name in agent_names:
        agent = AGENTS[agent_name]
        resolved_target_root = resolve_target_root(agent, home, target_root)
        print(f"Installing for {agent.label}...")
        installed = install_for_agent(source_root, resolved_target_root, agent)
        results.append((agent, installed))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install visual-prompt-cookbook for your AI agent.")
    parser.add_argument("--agent", type=parse_agent, help="Agent to install for. Use --list-agents to see choices.")
    parser.add_argument("--list-agents", action="store_true", help="List supported agents and exit.")
    parser.add_argument("--source-root", type=Path, help="Install from a local skill directory.")
    parser.add_argument(
        "--archive-url",
        help=(
            "Install from a VisualAI source archive. If omitted, the installer uses the local "
            f"checkout when available, otherwise downloads {DEFAULT_ARCHIVE_URL}."
        ),
    )
    parser.add_argument("--target-root", type=Path, help="Override the selected agent's target root directory.")
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_agents:
        print(list_agents())
        return

    selected_agent = args.agent
    interactive = selected_agent is None
    if selected_agent is None:
        selected_agent = choose_agent_interactively()

    try:
        target_root = args.target_root
        if selected_agent == "custom" and target_root is None:
            target_root = prompt_target_root_interactively()

        source_root, tmp = resolve_source_root(args.source_root, args.archive_url, verbose=interactive or bool(args.archive_url))
        try:
            results = install_selected_agents(
                selected_agent=selected_agent,
                source_root=source_root,
                home=args.home.expanduser().resolve(),
                target_root=target_root,
            )
        finally:
            if tmp is not None:
                tmp.cleanup()
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"error: {exc}\n")

    for agent, installed in results:
        print(f"Installed {SKILL_NAME} for {agent.label} to {installed}")


if __name__ == "__main__":
    main()
