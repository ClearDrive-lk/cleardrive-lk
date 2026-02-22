#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Running pre-commit checks (all files)..."
pre-commit run --all-files
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Running manual pytest hook..."
pre-commit run --hook-stage manual pytest --all-files -v
exit $LASTEXITCODE
