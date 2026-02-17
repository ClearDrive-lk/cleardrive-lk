#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Git hooks for ClearDrive.lk..."

if ! command -v python >/dev/null 2>&1; then
  echo "Python 3 is required."
  exit 1
fi

if ! command -v pre-commit >/dev/null 2>&1; then
  echo "Installing pre-commit..."
  python -m pip install pre-commit
fi

pre-commit install
pre-commit install --hook-type commit-msg

echo "Git hooks installed."
