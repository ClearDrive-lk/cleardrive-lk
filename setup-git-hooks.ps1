# setup-git-hooks.ps1
# Install and configure pre-commit hooks (Windows)

Write-Host " Setting up Git hooks for ClearDrive.lk..." -ForegroundColor Green
Write-Host ""

# ============================================================================
# CHECK PREREQUISITES
# ============================================================================

Write-Host "📋 Checking prerequisites..." -ForegroundColor Cyan

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host " Python 3 is not installed. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Node is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host " Node.js is not installed. Please install Node.js 20+" -ForegroundColor Red
    exit 1
}

Write-Host " Prerequisites OK" -ForegroundColor Green
Write-Host ""

# ============================================================================
# INSTALL PRE-COMMIT
# ============================================================================

Write-Host " Installing pre-commit..." -ForegroundColor Cyan

try {
    pip install pre-commit
    Write-Host " pre-commit installed" -ForegroundColor Green
} catch {
    Write-Host " Failed to install pre-commit" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# INSTALL GIT HOOKS
# ============================================================================

Write-Host "🔧 Installing Git hooks..." -ForegroundColor Cyan

try {
    pre-commit install
    Write-Host " Git hooks installed" -ForegroundColor Green
} catch {
    Write-Host " Failed to install Git hooks" -ForegroundColor Red
    exit 1
}

# Install commit-msg hook for conventional commits
try {
    pre-commit install --hook-type commit-msg
} catch {
    Write-Host "  Failed to install commit-msg hook (optional)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

Write-Host " Installing hook dependencies..." -ForegroundColor Cyan

# Backend dependencies
if (Test-Path "backend") {
    Write-Host "  Installing backend linting tools..." -ForegroundColor Gray
    pip install black isort flake8 mypy bandit safety pytest
}

# Frontend dependencies
if (Test-Path "apps/web") {
    Write-Host "  Installing frontend linting tools..." -ForegroundColor Gray
    Push-Location apps/web
    npm install --save-dev `
        eslint `
        prettier `
        "@typescript-eslint/parser" `
        "@typescript-eslint/eslint-plugin"
    Pop-Location
}

Write-Host " Dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# INITIALIZE SECRETS BASELINE
# ============================================================================

Write-Host " Creating secrets baseline..." -ForegroundColor Cyan

try {
    detect-secrets scan > .secrets.baseline 2>$null
} catch {
    Write-Host "  detect-secrets not found, skipping baseline creation" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# RUN INITIAL CHECK
# ============================================================================

Write-Host " Running initial pre-commit check on all files..." -ForegroundColor Cyan
Write-Host "   (This may take a few minutes on first run)" -ForegroundColor Gray
Write-Host ""

try {
    pre-commit run --all-files
} catch {
    Write-Host ""
    Write-Host "  Some checks failed. This is normal on first run." -ForegroundColor Yellow
    Write-Host "   Files have been auto-formatted where possible." -ForegroundColor Gray
    Write-Host "   Please review changes and commit them." -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# SUCCESS
# ============================================================================

Write-Host ""
Write-Host " Git hooks setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host " What happens now:" -ForegroundColor Cyan
Write-Host "   • Before each commit, pre-commit will automatically:"
Write-Host "     - Format Python code with Black"
Write-Host "     - Sort imports with isort"
Write-Host "     - Lint with Flake8"
Write-Host "     - Type check with mypy"
Write-Host "     - Check for security issues with Bandit"
Write-Host "     - Format frontend code with Prettier"
Write-Host "     - Lint frontend with ESLint"
Write-Host "     - Check for secrets"
Write-Host ""
Write-Host " Useful commands:" -ForegroundColor Cyan
Write-Host "   • Skip hooks (not recommended): git commit --no-verify"
Write-Host "   • Run hooks manually: pre-commit run --all-files"
Write-Host "   • Update hooks: pre-commit autoupdate"
Write-Host "   • Uninstall hooks: pre-commit uninstall"
Write-Host ""
Write-Host " You're all set! Happy coding!" -ForegroundColor Green
