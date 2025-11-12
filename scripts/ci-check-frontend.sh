#!/bin/bash
# Frontend-only CI Check Script
# Quick validation for frontend changes

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "🚀 Running Frontend CI Checks"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

cd "$PROJECT_ROOT/frontend"

# 1. ESLint
echo "1️⃣  Running ESLint..."
if npm run lint > /dev/null 2>&1; then
    print_status 0 "ESLint passed"
else
    echo -e "${RED}ESLint failed. Running with output:${NC}"
    npm run lint
    print_status 1 "ESLint failed"
fi
echo ""

# 2. TypeScript
echo "2️⃣  Running TypeScript type check..."
if npx tsc --noEmit > /dev/null 2>&1; then
    print_status 0 "TypeScript compilation passed"
else
    echo -e "${RED}TypeScript errors found:${NC}"
    npx tsc --noEmit
    print_status 1 "TypeScript compilation failed"
fi
echo ""

# 3. Tests with Coverage
echo "3️⃣  Running tests with coverage..."
echo "This may take a minute..."
if npm test -- --run --coverage > /tmp/test-output.log 2>&1; then
    # Show coverage summary
    grep -A 20 "% Statements" /tmp/test-output.log || true
    print_status 0 "Tests passed with coverage"
else
    echo -e "${RED}Tests failed. Output:${NC}"
    cat /tmp/test-output.log
    print_status 1 "Tests failed"
fi
echo ""

# 4. Build
echo "4️⃣  Building frontend..."
if npm run build > /tmp/build-output.log 2>&1; then
    print_status 0 "Build passed"
else
    echo -e "${RED}Build failed. Output:${NC}"
    tail -50 /tmp/build-output.log
    print_status 1 "Build failed"
fi
echo ""

# Summary
echo "========================================"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All frontend checks passed!${NC}"
    echo "Ready to push your changes."
    exit 0
else
    echo -e "${RED}✗ Some checks failed.${NC}"
    echo "Please fix the errors above before pushing."
    exit 1
fi
