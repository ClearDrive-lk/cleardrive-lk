"""Run a command only when the current Git branch is main.

Usage:
  python scripts/run_on_main.py --label "Bandit" -- <command> [args...]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _current_branch(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    branch = result.stdout.strip()
    return branch or None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="Hook")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("No command provided to run_on_main.py", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    branch = _current_branch(repo_root)

    # If git metadata is unavailable, run the command rather than silently skipping.
    if branch is None:
        print(f"{args.label}: could not determine branch; running check.")
        return subprocess.call(cmd, cwd=repo_root)

    if branch != "main":
        print(f"{args.label}: skipped on branch '{branch}' (runs on 'main' only).")
        return 0

    print(f"{args.label}: running on branch 'main'.")
    return subprocess.call(cmd, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
