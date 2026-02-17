<<<<<<< HEAD
﻿# setup-git-hooks.ps1
# Install and configure pre-commit hooks (Windows)

# Ensure this script is run with PowerShell
if ($PSVersionTable -eq $null) {
    Write-Host "ERROR: This script must be run with PowerShell." -ForegroundColor Red
    Write-Host "You appear to be using a different shell." -ForegroundColor Red
    Write-Host "Please open a PowerShell terminal and run '.\setup-git-hooks.ps1'" -ForegroundColor Yellow
    exit 1
}


=======
# setup-git-hooks.ps1
# Install and configure pre-commit hooks (Windows)

>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
Write-Host " Setting up Git hooks for ClearDrive.lk..." -ForegroundColor Green
Write-Host ""

# ============================================================================
# CHECK PREREQUISITES
# ============================================================================

<<<<<<< HEAD
Write-Host " Checking prerequisites..." -ForegroundColor Cyan
=======
Write-Host "📋 Checking prerequisites..." -ForegroundColor Cyan
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

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

<<<<<<< HEAD
# Check for virtual environment
if (-not ($env:VIRTUAL_ENV)) {
    Write-Host " It looks like you're not in a Python virtual environment." -ForegroundColor Yellow
    Write-Host " Please activate your venv (e.g., '.\venv312\Scripts\Activate.ps1') and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
# ============================================================================
# INSTALL PRE-COMMIT
# ============================================================================

<<<<<<< HEAD
if ($env:VIRTUAL_ENV) {
    $python = Join-Path $env:VIRTUAL_ENV "Scripts\\python.exe"
} else {
    $python = (Get-Command python -ErrorAction Stop).Source
}
if (-not (Test-Path $python)) {
    Write-Host " Python executable not found at: $python" -ForegroundColor Red
    exit 1
}
try {
    & $python -c "import sys; print(sys.executable)" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "python check failed"
    }
} catch {
    Write-Host " Python in your venv appears broken or points to a missing base install." -ForegroundColor Red
    Write-Host " Recreate the venv with your current Python and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host " Installing pre-commit..." -ForegroundColor Cyan

try {
    & $python -m pip install pre-commit
    if ($LASTEXITCODE -ne 0) {
        throw "pip install pre-commit failed"
    }
=======
Write-Host " Installing pre-commit..." -ForegroundColor Cyan

try {
    pip install pre-commit
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    Write-Host " pre-commit installed" -ForegroundColor Green
} catch {
    Write-Host " Failed to install pre-commit" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# INSTALL GIT HOOKS
# ============================================================================

<<<<<<< HEAD
Write-Host " Installing Git hooks..." -ForegroundColor Cyan
=======
Write-Host "🔧 Installing Git hooks..." -ForegroundColor Cyan
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

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
<<<<<<< HEAD
if (Test-Path "backend/requirements.txt") {
    Write-Host "  Installing backend dependencies..." -ForegroundColor Gray
    & $python -m pip install -r backend/requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "pip install requirements.txt failed"
    }
    if (Test-Path "backend/requirements-dev.txt") {
        & $python -m pip install -r backend/requirements-dev.txt
        if ($LASTEXITCODE -ne 0) {
            throw "pip install requirements-dev.txt failed"
        }
    }
}

# Frontend dependencies
if (Test-Path "apps/web/package.json") {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Gray
    Push-Location apps/web
    if (Test-Path "package-lock.json") {
        npm ci
    } else {
        npm install
    }
=======
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
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    Pop-Location
}

Write-Host " Dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# INITIALIZE SECRETS BASELINE
# ============================================================================

Write-Host " Creating secrets baseline..." -ForegroundColor Cyan

try {
<<<<<<< HEAD
    & $python -m pip install detect-secrets
    if ($LASTEXITCODE -ne 0) {
        throw "pip install detect-secrets failed"
    }
    # Scan the entire repository from the root. Errors will now be visible.
    & $python -m detect_secrets scan . > .secrets.baseline
    if ($LASTEXITCODE -ne 0) {
        throw "detect-secrets scan failed"
    }
=======
    detect-secrets scan > .secrets.baseline 2>$null
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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
<<<<<<< HEAD
Write-Host "   - Before each commit, pre-commit will automatically:"
=======
Write-Host "   • Before each commit, pre-commit will automatically:"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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
<<<<<<< HEAD
Write-Host "   - Skip hooks (not recommended): git commit --no-verify"
Write-Host "   - Run hooks manually: pre-commit run --all-files"
Write-Host "   - Update hooks: pre-commit autoupdate"
Write-Host "   - Uninstall hooks: pre-commit uninstall"
Write-Host ""
Write-Host "You're all set. Happy coding." -ForegroundColor Green
=======
Write-Host "   • Skip hooks (not recommended): git commit --no-verify"
Write-Host "   • Run hooks manually: pre-commit run --all-files"
Write-Host "   • Update hooks: pre-commit autoupdate"
Write-Host "   • Uninstall hooks: pre-commit uninstall"
Write-Host ""
Write-Host " You're all set! Happy coding!" -ForegroundColor Green
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
