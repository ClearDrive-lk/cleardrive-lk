#!/usr/bin/env pwsh
# Wrapper to run pre-commit from PowerShell (avoids Git-for-Windows MSYS2 crash).
# Used by .git/hooks/pre-commit when Git invokes the hook.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure we're in the repo root (Git runs hook with repo as cwd, but be defensive)
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot | Out-Null
try {
    pre-commit run --hook-stage pre-commit
    exit $LASTEXITCODE
} finally {
    Pop-Location | Out-Null
}
