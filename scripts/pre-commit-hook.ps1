#!/usr/bin/env pwsh
# Run only pre-commit-stage hooks during git commit.
# Use pre-commit's normal staged-file behavior during git commit.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot | Out-Null
try {
    pre-commit run --hook-stage pre-commit
    exit $LASTEXITCODE
} finally {
    Pop-Location | Out-Null
}
