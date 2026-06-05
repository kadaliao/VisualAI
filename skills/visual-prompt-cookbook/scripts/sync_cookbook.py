from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from cookbook_core import default_cookbook_root, sync_cookbook_assets


DEFAULT_REPO_URL = "git@github.com:kadaliao/AI-Visual-Prompt-Cookbook.git"


def git_commit_sha(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def clone_upstream(repo_url: str, target: Path) -> Path:
    checkout = target / "AI-Visual-Prompt-Cookbook"
    subprocess.check_call(["git", "clone", "--depth", "1", repo_url, str(checkout)])
    return checkout


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync AI Visual Prompt Cookbook assets into this skill.")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--source-dir", type=Path, help="Use an existing local Cookbook checkout.")
    parser.add_argument("--output-dir", type=Path, default=default_cookbook_root())
    parser.add_argument("--commit-sha", help="Commit SHA to record when --source-dir is not a git checkout.")
    args = parser.parse_args()

    if args.source_dir:
        source = args.source_dir.resolve()
        try:
            commit_sha = args.commit_sha or git_commit_sha(source)
        except subprocess.CalledProcessError:
            commit_sha = args.commit_sha or "local-source"
        upstream_url = args.repo_url
        result = sync_cookbook_assets(
            source_root=source,
            output_root=args.output_dir.resolve(),
            upstream_url=upstream_url,
            commit_sha=commit_sha,
        )
    else:
        with tempfile.TemporaryDirectory() as tmp:
            source = clone_upstream(args.repo_url, Path(tmp))
            result = sync_cookbook_assets(
                source_root=source,
                output_root=args.output_dir.resolve(),
                upstream_url=args.repo_url,
                commit_sha=git_commit_sha(source),
            )

    print(f"Synced {result['style_count']} styles from {result['commit_sha']} to {args.output_dir}")


if __name__ == "__main__":
    main()
