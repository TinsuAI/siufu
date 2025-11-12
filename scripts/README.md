# CI Check Scripts

These scripts help you run the same checks locally that the GitHub Actions CI pipeline runs, preventing failed builds and reducing unnecessary commits.

## Quick Start

### Frontend Only (Recommended for frontend changes)

```bash
# Option 1: Use npm script (from frontend directory)
cd frontend
npm run ci-check

# Option 2: Use shell script (from anywhere)
./scripts/ci-check-frontend.sh
```

### Backend Only (Recommended for backend changes)

```bash
# Option 1: Use Makefile (from backend directory)
cd backend
make ci-check

# Option 2: Use shell script (from anywhere)
./scripts/ci-check-backend.sh
```

### Full CI Check (Frontend + Backend)

```bash
./scripts/ci-check-local.sh
```

## What Gets Checked

### Frontend Checks (`ci-check-frontend.sh` or `npm run ci-check`)

1. **ESLint** - Code linting
2. **TypeScript** - Type checking (`tsc --noEmit`)
3. **Tests** - Unit tests with coverage (must pass 60% threshold)
4. **Build** - Production build verification

### Backend Checks (`ci-check-backend.sh` or `make ci-check`)

1. **Ruff** - Python linting (`ruff check src/ tests/`)
2. **Mypy** - Type checking (warnings only, doesn't fail)
3. **Pytest** - Unit tests with coverage

## When to Use

### Before Every Push

**Frontend changes:**
```bash
cd frontend
npm run ci-check
```

**Backend changes:**
```bash
cd backend
make ci-check
```

This ensures your code will pass CI before you push to GitHub.

### During Development

**Frontend:**
```bash
npm run type-check     # Quick type check
npm run test:coverage  # Run tests only
npm run lint           # Lint only
```

**Backend:**
```bash
make type-check   # Quick type check
make test-cov     # Run tests with coverage
make lint         # Lint only
make lint-fix     # Auto-fix linting issues
```

### Before Creating a PR
```bash
# Run full checks
./scripts/ci-check-local.sh
```

## Troubleshooting

### "Command not found: tsc"
Make sure you've installed dependencies:
```bash
cd frontend
npm install
```

### Backend tests skip
The backend tests require PostgreSQL and Redis to be running:
```bash
docker compose up -d postgres redis
```

### Permission denied
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

## CI Pipeline Alignment

These scripts mirror the exact checks from `.github/workflows/ci.yml`:

### Frontend

| CI Pipeline Step | Shell Script | npm/make Command |
|-----------------|--------------|------------------|
| ESLint | `./scripts/ci-check-frontend.sh` | `npm run lint` |
| TypeScript | `./scripts/ci-check-frontend.sh` | `npm run type-check` |
| Tests + Coverage | `./scripts/ci-check-frontend.sh` | `npm run test:coverage` |
| Build | `./scripts/ci-check-frontend.sh` | `npm run build` |
| **All Frontend** | `./scripts/ci-check-frontend.sh` | `npm run ci-check` |

### Backend

| CI Pipeline Step | Shell Script | make Command |
|-----------------|--------------|--------------|
| Ruff Linting | `./scripts/ci-check-backend.sh` | `make lint` |
| Mypy Type Check | `./scripts/ci-check-backend.sh` | `make type-check` |
| Pytest + Coverage | `./scripts/ci-check-backend.sh` | `make test-cov` |
| **All Backend** | `./scripts/ci-check-backend.sh` | `make ci-check` |

## Pro Tips

1. **Use pre-commit hooks** - Husky is already configured to run checks before commits
2. **Run `ci-check` before pushing** - Saves time by catching errors locally
3. **Watch mode during development** - Use `npm run test:watch` for instant feedback
4. **Coverage reports** - Check `frontend/coverage/` after running tests

## Exit Codes

- `0` - All checks passed ✅
- `1` - One or more checks failed ❌

You can use this in scripts:
```bash
if npm run ci-check; then
  git push
else
  echo "Fix errors before pushing!"
fi
```
