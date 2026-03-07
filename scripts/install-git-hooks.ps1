#!/usr/bin/env pwsh
# Installs Git hooks with PowerShell wrapper (avoids Git-for-Windows MSYS2 crash).
# Run this instead of pre-commit install on Windows.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot | Out-Null
try {
    # Install pre-commit hooks (generates default sh-based hooks)
    Write-Host "Installing pre-commit..."
    pre-commit install
    pre-commit install --hook-type commit-msg

    # Patch pre-commit to delegate to PowerShell (avoids MSYS2 crash)
    $hooksDir = Join-Path (Join-Path $repoRoot ".git") "hooks"
    $preCommitHook = Join-Path $hooksDir "pre-commit"
    $preCommitPs1 = Join-Path (Join-Path $repoRoot "scripts") "pre-commit-hook.ps1"

    $wrapperContent = @"
#!/bin/sh
# Patched: delegate to PowerShell to avoid Git-for-Windows MSYS2 crash
exec powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/pre-commit-hook.ps1"
"@

    [System.IO.File]::WriteAllText($preCommitHook, $wrapperContent)
    Write-Host "Patched pre-commit hook to use PowerShell wrapper."

    # Patch pre-push similarly if it exists
    $prePushHook = Join-Path $hooksDir "pre-push"
    if (Test-Path $prePushHook) {
        $prePushContent = @"
#!/bin/sh
exec powershell -NoProfile -ExecutionPolicy Bypass -Command "pre-commit run --hook-stage pre-push"
"@
        [System.IO.File]::WriteAllText($prePushHook, $prePushContent)
        Write-Host "Patched pre-push hook to use PowerShell wrapper."
    }

    Write-Host "Git hooks installed (PowerShell wrapper active)."
} finally {
    Pop-Location | Out-Null
}
