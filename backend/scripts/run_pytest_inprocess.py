#!/usr/bin/env python3
"""Run pytest in-process to avoid subprocess pipe crashes."""
import os
import sys
from pathlib import Path

# Get output file path
output_file = sys.argv[1] if len(sys.argv) > 1 else None

# Set test environment before importing pytest
os.environ.update({
    "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/cleardrive_test",  # pragma: allowlist secret
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "test",
    "PYTHONUNBUFFERED": "1",  # Ensure unbuffered output
})

# Change to backend directory
repo_root = Path(__file__).resolve().parents[2]
backend_dir = repo_root / "backend"
os.chdir(backend_dir)

# Write initial message to output file immediately
if output_file:
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Starting pytest in-process...\n")
            f.flush()
    except Exception as e:
        pass  # Ignore errors writing initial message

# Import pytest and run it in-process
try:
    import pytest
except Exception as e:
    if output_file:
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"ERROR: Failed to import pytest: {e}\n")
                f.flush()
        except Exception:
            pass
    sys.exit(1)

# Configure pytest arguments
# Use --capture=no to ensure output goes directly to stdout/stderr (which we've redirected)
pytest_args = [
    "-o", "addopts=",
    "-v",
    "-ra",
    "--strict-markers",
    "--tb=short",
    "-p", "no:warnings",
    "--capture=no",  # Disable pytest's output capturing to ensure we see everything
]

# Redirect stdout/stderr to file if provided
if output_file:
    # Append to existing file (we already wrote initial message)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    try:
        # Open file with append mode and line buffering for immediate writes
        f = open(output_file, 'a', encoding='utf-8', buffering=1)
        try:
            f.write("Pytest imported successfully, starting test run...\n")
            f.flush()
            sys.stdout = f
            sys.stderr = f
            exit_code = pytest.main(pytest_args)
            # Write completion message
            f.write(f"\n\nPytest completed with exit code: {exit_code}\n")
            # Ensure everything is flushed
            sys.stdout.flush()
            sys.stderr.flush()
            f.flush()
            import os
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            # Restore stdout/stderr before closing file
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            f.close()
    except Exception as e:
        # Restore stdout/stderr first in case of exception
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        # Write error to file if possible
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"ERROR running pytest: {e}\n")
                import traceback
                f.write(traceback.format_exc())
                f.flush()
        except Exception:
            pass
        exit_code = 1
else:
    exit_code = pytest.main(pytest_args)

sys.exit(exit_code)
