"""Run backend pytest with CI-aligned defaults from repository root."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _has_sqlalchemy(python_exe: str) -> bool:
    """Return True if the interpreter can import sqlalchemy."""
    try:
        result = subprocess.run(
            [python_exe, "-c", "import sqlalchemy"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _pick_python(repo_root: Path, backend_dir: Path) -> str:
    """
    Pick a Python interpreter that has backend deps.

    Preference:
    1. Active virtualenv (if it has sqlalchemy)
    2. Common project venv locations (cross-platform)
    3. Current interpreter (CI/system fallback)
    """
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

    # Last fallback: current interpreter (works in CI where deps are installed).
    candidates.append(Path(sys.executable))

    for candidate in candidates:
        if candidate.exists() and _has_sqlalchemy(str(candidate)):
            return str(candidate)

    return str(sys.executable)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"
    python_exe = _pick_python(repo_root, backend_dir)

    # Match GitHub Actions backend test environment defaults.
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
        "--cov=app",
        "--cov-report=xml",
        "--cov-report=html",
        "--cov-report=term",
    ]
    return subprocess.call(cmd, cwd=backend_dir, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
