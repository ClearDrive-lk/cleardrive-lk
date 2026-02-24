#!/usr/bin/env python3
"""Minimal pytest runner that avoids git hook crashes by complete isolation."""
import os
import sys
import subprocess
from pathlib import Path

# Set test environment
os.environ.update({
    "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/cleardrive_test",  # pragma: allowlist secret
    "REDIS_URL": "redis://localhost:6379/0",
    "ENVIRONMENT": "test",
})

# Get paths
repo_root = Path(__file__).resolve().parents[2]
backend_dir = repo_root / "backend"
python_exe = sys.executable

# Output file
output_file = sys.argv[1] if len(sys.argv) > 1 else str(repo_root / "pytest_output.txt")

# Run pytest with complete isolation
cmd = [
    python_exe,
    "-m",
    "pytest",
    "-o", "addopts=",
    "-v",
    "-ra",
    "--strict-markers",
    "--tb=short",
    "-p", "no:warnings",
]

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        result = subprocess.run(
            cmd,
            cwd=str(backend_dir),
            stdout=f,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            timeout=120,
            creationflags=0x08000000 if sys.platform == 'win32' else 0,
        )
    sys.exit(result.returncode)
except Exception as e:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Error running pytest: {e}\n")
    sys.exit(1)
