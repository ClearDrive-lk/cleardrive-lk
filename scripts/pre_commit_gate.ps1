#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
    pre-commit run --hook-stage pre-commit --all-files
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
