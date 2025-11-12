#!/bin/bash
# Local CI Check Script
# Run this before pushing to avoid CI failures
# This script mimics the GitHub Actions CI pipeline

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "🚀 Running Local CI Checks"
echo "========================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        OVERALL_STATUS=1
    fi
}

echo "========================================"
echo "📦 FRONTEND CHECKS"
echo "========================================"
echo ""

cd "$PROJECT_ROOT/frontend"

# 1. Frontend Linting
echo "1️⃣  Running ESLint..."
if npm run lint; then
    print_status 0 "ESLint passed"
else
    print_status 1 "ESLint failed"
fi
echo ""

# 2. TypeScript Type Checking
echo "2️⃣  Running TypeScript type check..."
if npx tsc --noEmit; then
    print_status 0 "TypeScript compilation passed"
else
    print_status 1 "TypeScript compilation failed"
fi
echo ""

# 3. Frontend Tests with Coverage
echo "3️⃣  Running frontend tests with coverage..."
if npm test -- --run --coverage; then
    print_status 0 "Frontend tests passed"
else
    print_status 1 "Frontend tests failed"
fi
echo ""

# 4. Frontend Build
echo "4️⃣  Building frontend..."
if npm run build; then
    print_status 0 "Frontend build passed"
else
    print_status 1 "Frontend build failed"
fi
echo ""

echo "========================================"
echo "🐍 BACKEND CHECKS"
echo "========================================"
echo ""

cd "$PROJECT_ROOT/backend"

# 5. Backend Linting (Ruff)
echo "5️⃣  Running Ruff linter..."
if ruff check src/ tests/; then
    print_status 0 "Ruff linting passed"
else
    print_status 1 "Ruff linting failed"
fi
echo ""

# 6. Type Checking (mypy) - warning only
echo "6️⃣  Running mypy type checker (warning only)..."
if mypy src/; then
    print_status 0 "Mypy type check passed"
else
    echo -e "${YELLOW}⚠ Mypy type check has warnings (not failing CI)${NC}"
fi
echo ""

# 7. Backend Tests with Coverage
echo "7️⃣  Running backend tests with coverage..."
echo "Note: Requires PostgreSQL and Redis running"
echo "Starting services if needed..."

# Check if services are running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ PostgreSQL not running. Skipping backend tests.${NC}"
    echo "To run backend tests, start services with:"
    echo "  docker compose up -d postgres redis"
else
    if pytest tests/ --cov=src --cov-report=term-missing -v --tb=short; then
        print_status 0 "Backend tests passed"
    else
        print_status 1 "Backend tests failed"
    fi
fi
echo ""

# Final Summary
echo "========================================"
echo "📊 SUMMARY"
echo "========================================"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix errors before pushing.${NC}"
    exit 1
fi
