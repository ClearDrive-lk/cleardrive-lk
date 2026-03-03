"""
Run Alembic migrations with explicit env profile mode.

Usage:
  python scripts/migrate_runner.py --mode local
  python scripts/migrate_runner.py --mode supabase
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run alembic upgrade head with selected env profile")
    parser.add_argument("--mode", choices=["local", "supabase"], required=True)
    args = parser.parse_args()

    mode_env = ROOT / (".env.localdb" if args.mode == "local" else ".env.supabase")
    fallback_env = ROOT / ".env"
    _load_env_file(mode_env)
    _load_env_file(fallback_env)

    cmd = [sys.executable, "-m", "alembic", "-c", str(ROOT / "alembic.ini"), "upgrade", "head"]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    main()
