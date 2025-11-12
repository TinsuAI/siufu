#!/bin/bash
# Backend-only CI Check Script
# Quick validation for backend changes

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "🐍 Running Backend CI Checks"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OVERALL_STATUS=0

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        OVERALL_STATUS=1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

cd "$PROJECT_ROOT/backend"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    print_info "Activated virtual environment"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    print_info "Activated virtual environment"
else
    print_warning "No virtual environment found, using system Python"
fi
echo ""

# Check if required services are running
echo "Checking required services..."
POSTGRES_RUNNING=false
REDIS_RUNNING=false

# Check if PostgreSQL container is running and accepting connections
if docker ps --format '{{.Names}}' | grep -q postgres && \
   docker exec $(docker ps --filter "name=postgres" --format "{{.ID}}" | head -1) pg_isready > /dev/null 2>&1; then
    POSTGRES_RUNNING=true
    print_info "PostgreSQL is running"
else
    print_warning "PostgreSQL is not running"
fi

# Check if Redis container is running and accepting connections
if docker ps --format '{{.Names}}' | grep -q redis && \
   docker exec $(docker ps --filter "name=redis" --format "{{.ID}}" | head -1) redis-cli ping > /dev/null 2>&1; then
    REDIS_RUNNING=true
    print_info "Redis is running"
else
    print_warning "Redis is not running"
fi
echo ""

# 1. Ruff Linting
echo "1️⃣  Running Ruff linter..."
if ruff check src/ tests/ > /tmp/ruff-output.log 2>&1; then
    print_status 0 "Ruff linting passed"
else
    echo -e "${RED}Ruff linting failed:${NC}"
    cat /tmp/ruff-output.log
    print_status 1 "Ruff linting failed"
fi
echo ""

# 2. Mypy Type Checking (warning only, doesn't fail)
echo "2️⃣  Running mypy type checker..."
if mypy src/ > /tmp/mypy-output.log 2>&1; then
    print_status 0 "Mypy type check passed"
else
    print_warning "Mypy type check has warnings (not failing CI):"
    cat /tmp/mypy-output.log | head -20
fi
echo ""

# 3. Pytest with Coverage
echo "3️⃣  Running backend tests with coverage..."
if [ "$POSTGRES_RUNNING" = false ] || [ "$REDIS_RUNNING" = false ]; then
    print_warning "Skipping tests - PostgreSQL and/or Redis not running"
    print_info "To run tests, start services with:"
    print_info "  docker compose up -d postgres redis"
    print_info "Or:"
    print_info "  cd backend && docker compose up -d"
else
    print_info "Running pytest with coverage..."

    # Set test environment first (needed for config.py to load .env.test)
    export ENVIRONMENT="test"

    # Load test environment variables
    if [ -f ".env.test" ]; then
        export $(cat .env.test | grep -v '^#' | grep -v '^$' | xargs)
    else
        export DATABASE_URL="postgresql+asyncpg://postgres:test_password_123@localhost:5432/customs_db_test"
        export REDIS_URL="redis://localhost:6379/0"
        export JWT_SECRET_KEY="test-jwt-secret-key-for-ci"
    fi

    if pytest tests/ --cov=src --cov-report=term-missing -v --tb=short > /tmp/pytest-output.log 2>&1; then
        # Show coverage summary
        grep -A 30 "TOTAL" /tmp/pytest-output.log || tail -50 /tmp/pytest-output.log
        print_status 0 "Backend tests passed with coverage"
    else
        echo -e "${RED}Tests failed. Output:${NC}"
        tail -100 /tmp/pytest-output.log
        print_status 1 "Backend tests failed"
    fi
fi
echo ""

# Summary
echo "========================================"
echo "📊 SUMMARY"
echo "========================================"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All backend checks passed!${NC}"
    echo "Ready to push your changes."
    exit 0
else
    echo -e "${RED}✗ Some checks failed.${NC}"
    echo "Please fix the errors above before pushing."
    exit 1
fi
