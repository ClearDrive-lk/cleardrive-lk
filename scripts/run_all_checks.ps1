#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Running pre-commit checks (all files)..."
pre-commit run --all-files
exit $LASTEXITCODE
