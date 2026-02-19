"""Run backend dependency vulnerability checks with Safety in non-interactive mode."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    cmd = [
        sys.executable,
        "-m",
        "safety",
        "check",
        "-r",
        "requirements.txt",
        "-r",
        "requirements-dev.txt",
        "--full-report",
    ]
    return subprocess.call(cmd, cwd=backend_dir)


if __name__ == "__main__":
    raise SystemExit(main())
