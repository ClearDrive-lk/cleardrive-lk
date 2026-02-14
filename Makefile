# Makefile
# Common development commands for ClearDrive.lk

.PHONY: help setup install-hooks lint format test clean

# Default target
help:
	@echo "ClearDrive.lk Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial project setup (install hooks + deps)"
	@echo "  make install-hooks  - Install pre-commit Git hooks"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-lint   - Run all backend linters"
	@echo "  make backend-format - Format backend code"
	@echo "  make backend-test   - Run backend tests"
	@echo "  make backend-run    - Run backend server"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-lint  - Run all frontend linters"
	@echo "  make frontend-format- Format frontend code"
	@echo "  make frontend-test  - Run frontend tests"
	@echo "  make frontend-run   - Run frontend dev server"
	@echo ""
	@echo "Combined:"
	@echo "  make lint           - Run all linters (backend + frontend)"
	@echo "  make format         - Format all code"
	@echo "  make test           - Run all tests"
	@echo "  make run            - Run both backend and frontend"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove generated files"
	@echo "  make clean-hooks    - Uninstall Git hooks"

# ============================================================================
# SETUP
# ============================================================================

setup: install-hooks
	@echo "✅ Project setup complete!"

install-hooks:
	@echo "🔧 Installing Git hooks..."
	@chmod +x setup-git-hooks.sh
	@./setup-git-hooks.sh

# ============================================================================
# BACKEND
# ============================================================================

backend-lint:
	@echo "🔍 Running backend linters..."
	@cd backend && black --check app/
	@cd backend && isort --check app/
	@cd backend && flake8 app/
	@cd backend && mypy app/ --explicit-package-bases --ignore-missing-imports

backend-format:
	@echo "✨ Formatting backend code..."
	@cd backend && black app/
	@cd backend && isort app/

backend-test:
	@echo "🧪 Running backend tests..."
	@cd backend && pytest -v

backend-test-cov:
	@echo "🧪 Running backend tests with coverage..."
	@cd backend && pytest --cov=app --cov-report=html --cov-report=term

backend-run:
	@echo "🚀 Starting backend server..."
	@cd backend && uvicorn app.main:app --reload

backend-migrate:
	@echo "🗄️  Running database migrations..."
	@cd backend && alembic upgrade head

backend-migration:
	@echo "📝 Creating new migration..."
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

# ============================================================================
# FRONTEND
# ============================================================================

frontend-lint:
	@echo "🔍 Running frontend linters..."
	@cd apps/web && npx eslint app
	@cd apps/web && npx prettier . --check

frontend-format:
	@echo "✨ Formatting frontend code..."
	@cd apps/web && npx prettier . --write

frontend-test:
	@echo "🧪 Running frontend tests..."
	@cd apps/web && npm test

frontend-run:
	@echo "🚀 Starting frontend dev server..."
	@cd apps/web && npm run dev

frontend-build:
	@echo "🏗️  Building frontend..."
	@cd apps/web && npm run build

# ============================================================================
# COMBINED
# ============================================================================

lint: backend-lint frontend-lint
	@echo "✅ All linting complete!"

format: backend-format frontend-format
	@echo "✅ All code formatted!"

test: backend-test frontend-test
	@echo "✅ All tests complete!"

run:
	@echo "🚀 Starting both servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@make -j 2 backend-run frontend-run

# ============================================================================
# SECURITY
# ============================================================================

security-scan:
	@echo "🔒 Running security scans..."
	@cd backend && bandit -r app/ -ll
	@cd backend && safety check
	@cd apps/web && npm audit

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "🧹 Cleaning generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-hooks:
	@echo "🗑️  Uninstalling Git hooks..."
	@pre-commit uninstall
	@pre-commit uninstall --hook-type commit-msg
	@echo "✅ Git hooks removed!"

# ============================================================================
# PRE-COMMIT
# ============================================================================

pre-commit-all:
	@echo "🔍 Running pre-commit on all files..."
	@pre-commit run --all-files

pre-commit-update:
	@echo "📦 Updating pre-commit hooks..."
	@pre-commit autoupdate
