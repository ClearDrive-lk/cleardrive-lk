#!/usr/bin/env pwsh
param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot | Out-Null

try {
    Write-Host "Running full local checks..."
    & "$repoRoot\scripts\run_all_checks.ps1"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Checks failed. Commit aborted."
        exit $LASTEXITCODE
    }

    Write-Host "Checks passed. Staging changes..."
    git add .

    Write-Host "Creating commit..."
    git commit --no-verify -m $Message

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Commit failed (possibly no staged changes)."
        exit $LASTEXITCODE
    }

    Write-Host "✅ Commit created successfully."
    exit 0
}
finally {
    Pop-Location | Out-Null
}
