"""Run backend pytest with CI-aligned defaults from repository root."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _has_backend_test_deps(python_exe: str) -> bool:
    """Return True if the interpreter has core backend test dependencies."""
    try:
        result = subprocess.run(
            [python_exe, "-c", "import pytest, sqlalchemy, supabase"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _pick_python(repo_root: Path, backend_dir: Path) -> str:
    """Pick a Python interpreter that has backend test deps."""
    candidates: list[Path] = []

    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        ve = Path(virtual_env)
        candidates.extend([ve / "Scripts" / "python.exe", ve / "bin" / "python"])

    for name in (".venv", "venv", "venv312"):
        candidates.extend(
            [
                repo_root / name / "Scripts" / "python.exe",
                repo_root / name / "bin" / "python",
                backend_dir / name / "Scripts" / "python.exe",
                backend_dir / name / "bin" / "python",
            ]
        )

    candidates.append(Path(sys.executable))

    for candidate in candidates:
        if candidate.exists() and _has_backend_test_deps(str(candidate)):
            return str(candidate)

    return str(sys.executable)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend pytest tests")
    parser.add_argument(
        "--skip-coverage",
        action="store_true",
        help="Skip coverage reports (faster local run)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"
    python_exe = _pick_python(repo_root, backend_dir)

    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/cleardrive_test",  # pragma: allowlist secret
            "REDIS_URL": "redis://localhost:6379/0",
            "JWT_SECRET_KEY": "test-secret-key-min-32-characters-long",  # pragma: allowlist secret
            "ENCRYPTION_KEY": "test-encryption-key-32-chars!!",  # pragma: allowlist secret
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",  # pragma: allowlist secret
            "PAYHERE_MERCHANT_ID": "test-merchant-id",
            "PAYHERE_MERCHANT_SECRET": "test-merchant-secret",  # pragma: allowlist secret
            "ANTHROPIC_API_KEY": "test-api-key",  # pragma: allowlist secret
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_USERNAME": "test@gmail.com",
            "SMTP_PASSWORD": "test-password",  # pragma: allowlist secret
            "ADMIN_EMAILS": "cleardrivelk@gmail.com",
            "ENVIRONMENT": "test",
            "COVERAGE_RCFILE": str(repo_root / ".coveragerc"),
        }
    )

    cmd = [
        python_exe,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-q",
        "-ra",
        "--strict-markers",
        "--tb=short",
        "-p",
        "no:warnings",
    ]
    if not args.skip_coverage:
        cmd.extend(["--cov=app", "--cov-report=xml", "--cov-report=html"])

    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        print("Backend tests timed out after 180s in hook.")
        print("Run `pre-commit run --hook-stage manual pytest --all-files -v` to debug.")
        return 124

    if result.returncode == 0:
        print("Backend tests passed.")
        return 0

    print("Backend tests failed in hook.")
    print("Run `pre-commit run --hook-stage manual pytest --all-files -v` for details.")
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
