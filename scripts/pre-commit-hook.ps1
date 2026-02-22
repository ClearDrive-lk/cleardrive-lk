#!/usr/bin/env pwsh
# Wrapper to run pre-commit from PowerShell (avoids Git-for-Windows MSYS2 crash).
# Runs pre-commit in a process with REDIRECTED I/O so it inherits no pipes from Git -
# that pipe inheritance causes pytest to crash (exit 3221226505).
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outFile = [System.IO.Path]::GetTempFileName()
$errFile = [System.IO.Path]::GetTempFileName()
try {
    $proc = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "& { Set-Location '$repoRoot'; pre-commit run --hook-stage pre-commit --all-files; exit `$LASTEXITCODE }" -Wait -PassThru -NoNewWindow -RedirectStandardOutput $outFile -RedirectStandardError $errFile
    Get-Content $outFile | Write-Host
    $errContent = Get-Content $errFile -Raw -ErrorAction SilentlyContinue
    if ($errContent) { Write-Host $errContent }
    exit $proc.ExitCode
} finally {
    Remove-Item $outFile, $errFile -ErrorAction SilentlyContinue
}
