#!/usr/bin/env pwsh
# Run only pre-commit-stage hooks during git commit.
# Pytest is manual-only in .pre-commit-config.yaml and should not be forced here.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot | Out-Null
try {
    pre-commit run --hook-stage pre-commit --all-files
    exit $LASTEXITCODE
} finally {
    Pop-Location | Out-Null
}
