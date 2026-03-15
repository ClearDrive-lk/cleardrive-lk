$ErrorActionPreference = "Stop"

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "==================================="
Write-Host "EXTERNAL RESOURCES AUDIT"
Write-Host "==================================="
Write-Host ""

Write-Host "Searching for external scripts..."
rg -n 'src="https?://' $rootDir\app $rootDir\components $rootDir\public || Write-Host "None found in src="

Write-Host ""
Write-Host "Searching for external stylesheets..."
rg -n 'href="https?://' $rootDir\app $rootDir\components $rootDir\public || Write-Host "None found in href="

Write-Host ""
Write-Host "Searching for CDN imports..."
rg -n 'cdn\.jsdelivr|unpkg\.com|cdnjs\.cloudflare|googletagmanager|fonts\.googleapis|accounts\.google\.com' $rootDir\app $rootDir\components $rootDir\public || Write-Host "No CDN imports found"

Write-Host ""
Write-Host "==================================="
Write-Host "AUDIT COMPLETE"
Write-Host "==================================="
