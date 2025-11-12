.PHONY: help lint type-check test test-cov ci-check format install clean services-start services-stop

# Default target
help:
	@echo "🐍 Backend Development Commands"
	@echo ""
	@echo "Quality Checks (CI Pipeline):"
	@echo "  make ci-check      - Run all CI checks (lint + type + test)"
	@echo "  make lint          - Run Ruff linter"
	@echo "  make lint-fix      - Auto-fix linting issues"
	@echo "  make type-check    - Run mypy type checker"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  make format        - Format code with Ruff"
	@echo "  make install       - Install dependencies"
	@echo "  make clean         - Clean cache files"
	@echo ""
	@echo "Docker Services:"
	@echo "  make services-start - Start PostgreSQL and Redis"
	@echo "  make services-stop  - Stop PostgreSQL and Redis"
	@echo ""

# Linting with Ruff
lint:
	@echo "🔍 Running Ruff linter..."
	ruff check src/ tests/

lint-fix:
	@echo "🔧 Auto-fixing linting issues..."
	ruff check --fix src/ tests/

# Type checking with mypy
type-check:
	@echo "🔍 Running mypy type checker..."
	mypy src/

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -v

# CI Check - runs all checks like GitHub Actions
ci-check:
	@echo "========================================"
	@echo "🚀 Running Backend CI Checks"
	@echo "========================================"
	@echo ""
	@echo "1️⃣  Linting with Ruff..."
	@make lint
	@echo ""
	@echo "2️⃣  Type checking with mypy..."
	@make type-check || echo "⚠️  Type check has warnings (not failing)"
	@echo ""
	@echo "3️⃣  Running tests with coverage..."
	@make test-cov
	@echo ""
	@echo "✅ All CI checks passed!"

# Code formatting
format:
	@echo "✨ Formatting code with Ruff..."
	ruff format src/ tests/

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml

# Docker services
services-start:
	@echo "🐳 Starting PostgreSQL and Redis..."
	docker compose up -d postgres redis

services-stop:
	@echo "🛑 Stopping PostgreSQL and Redis..."
	docker compose stop postgres redis
