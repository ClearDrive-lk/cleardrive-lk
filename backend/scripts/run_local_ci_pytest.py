"""Run backend pytest with CI-aligned defaults from repository root."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _has_backend_test_deps(python_exe: str) -> bool:
    """Return True if the interpreter has core backend test dependencies."""
    try:
        result = subprocess.run(
            [python_exe, "-c", "import pytest, sqlalchemy, supabase"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,  # Timeout after 5 seconds to avoid hanging
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _pick_python(repo_root: Path, backend_dir: Path) -> str:
    """
    Pick a Python interpreter that has backend test deps.

    Preference:
    1. Active virtualenv (if it has test deps)
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
        if candidate.exists() and _has_backend_test_deps(str(candidate)):
            return str(candidate)

    return str(sys.executable)


def main() -> int:
    # Print immediately so we know the script started (flushed to avoid buffering)
    print("Starting pytest runner...", flush=True)

    parser = argparse.ArgumentParser(description="Run backend pytest tests")
    parser.add_argument(
        "--skip-coverage",
        action="store_true",
        help="Skip coverage reports (faster, for pre-commit hooks)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    print(f"Picking Python interpreter...", flush=True)
    python_exe = _pick_python(repo_root, backend_dir)
    print(f"Using Python: {python_exe}", flush=True)

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

    # Create output file path for pytest to write to
    import tempfile
    pytest_output_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
    pytest_output_path = pytest_output_file.name
    pytest_output_file.close()

    cmd = [
        python_exe,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-v",  # Verbose - show each test name
        "-ra",  # Show extra test summary info for all tests
        "--strict-markers",
        "--tb=short",  # Short traceback format
        "-p",
        "no:warnings",
        "--junit-xml", pytest_output_path.replace('.txt', '.xml'),  # Write results to XML
    ]

    # Only add coverage in CI, not in pre-commit hooks (faster, avoids hangs)
    if not args.skip_coverage:
        cmd.extend(["--cov=app", "--cov-report=xml", "--cov-report=html"])

    print(f"Running pytest with command: {' '.join(cmd)}", flush=True)
    print(f"Working directory: {backend_dir}", flush=True)

    # Use a reasonable timeout for pre-commit hooks (120s) - tests should complete quickly
    # If they take longer, something is wrong (database/Redis connection issues, etc.)
    timeout_seconds = 120 if args.skip_coverage else 180

    # Capture pytest output to avoid crash (exit 3221226505) when streaming
    # large output through the hook pipeline (even with PowerShell wrapper).
    # But capture to temp file so we can show it on failure.
    out_path = None
    try:
        # Create temp file for output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            out_path = tmp_file.name

        print(f"Starting pytest (timeout: {timeout_seconds}s)...", flush=True)

        # Run pytest and capture output
        # Use unbuffered Python to ensure output is written immediately
        if cmd[0].endswith('python.exe') or cmd[0].endswith('python'):
            # Insert -u flag for unbuffered output
            python_idx = 0
            if cmd[python_idx] == python_exe:
                # Add -u flag after python for unbuffered output
                cmd.insert(1, '-u')

        print("Executing pytest command...", flush=True)
        # Use simple file write - pytest will write directly to the file
        # This avoids any pipe inheritance issues
        # On Windows, use CREATE_NO_WINDOW to prevent console window and handle inheritance issues
        creation_flags = 0
        if sys.platform == 'win32':
            # CREATE_NO_WINDOW = 0x08000000 prevents console window creation
            # This also helps avoid handle inheritance issues that cause crashes
            creation_flags = 0x08000000

        # Redirect to DEVNULL to avoid git hook crashes, pytest will write to its own files
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,  # Avoid pipe crashes
            stderr=subprocess.DEVNULL,  # Avoid pipe crashes
            check=False,
            timeout=timeout_seconds,
            creationflags=creation_flags if sys.platform == 'win32' else 0,
        )

        # Read output from the file pytest wrote to (if it exists)
        # For now, just indicate tests ran
        output = ""
        junit_xml_path = pytest_output_path.replace('.txt', '.xml')
        if os.path.exists(junit_xml_path):
            # Could parse XML here if needed
            output = f"Tests completed. Results written to {junit_xml_path}\n"
            try:
                os.remove(junit_xml_path)
            except Exception:
                pass

        # Also try to read from the temp file if pytest wrote there
        if os.path.exists(pytest_output_path):
            try:
                with open(pytest_output_path, 'r', encoding='utf-8') as f:
                    file_output = f.read()
                    if file_output:
                        output = file_output
            except Exception:
                pass
            try:
                os.remove(pytest_output_path)
            except Exception:
                pass
            finally:
                # Ensure file is flushed
                out_file.flush()
                import os
                try:
                    os.fsync(out_file.fileno())
                except Exception:
                    pass  # Ignore fsync errors

        # Output already read above in binary mode

    except subprocess.TimeoutExpired:
        print(f"Backend tests timed out after {timeout_seconds}s.", flush=True)
        # Try to read partial output immediately
        output = ""
        if out_path and os.path.exists(out_path):
            try:
                with open(out_path, 'r', encoding='utf-8') as f:
                    output = f.read()
            except Exception as e:
                output = f"Error reading output file: {e}"

        print("\n--- Partial test output (if any) ---", flush=True)
        if output:
            print(output, flush=True)
        else:
            print("No output captured - pytest may have hung before producing any output.", flush=True)
        print("--- End of partial output ---", flush=True)
        print("\nThis usually indicates:", flush=True)
        print("1. Database/Redis connection issues", flush=True)
        print("2. Tests waiting for resources that aren't available", flush=True)
        print("3. Deadlock or infinite loop in test setup", flush=True)
        print("\nTry running: python backend\\scripts\\run_local_ci_pytest.py --skip-coverage", flush=True)
        return 124
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
    finally:
        # Clean up temp file
        if out_path and os.path.exists(out_path):
            try:
                os.unlink(out_path)
            except Exception:
                pass

    if result.returncode == 0:
        print("Backend tests passed.")
        return 0

    # Tests failed - show the output
    print("Backend tests failed in pre-push hook.")
    print("\n--- Test output ---")
    print(output)
    print("--- End of test output ---")
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
