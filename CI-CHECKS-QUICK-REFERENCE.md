# CI Checks - Quick Reference

> **TL;DR:** Run these commands before pushing to avoid CI failures

## Frontend

```bash
cd frontend
npm run ci-check
```

**Individual checks:**
```bash
npm run lint          # ESLint
npm run type-check    # TypeScript
npm run test:coverage # Tests with coverage
npm run build         # Production build
```

## Backend

```bash
cd backend
make ci-check
```

**Individual checks:**
```bash
make lint        # Ruff linter
make type-check  # Mypy type checker
make test-cov    # Tests with coverage
make lint-fix    # Auto-fix linting issues
```

**Note:** Backend tests require Docker services:
```bash
make services-start  # Start PostgreSQL + Redis
make services-stop   # Stop services
```

## Full Stack

```bash
./scripts/ci-check-local.sh  # Run all checks (frontend + backend)
```

## Alternative: Shell Scripts (work from anywhere)

```bash
./scripts/ci-check-frontend.sh  # Frontend only
./scripts/ci-check-backend.sh   # Backend only
./scripts/ci-check-local.sh     # Both
```

## What Gets Checked

| Check | Frontend | Backend |
|-------|----------|---------|
| Linting | ESLint (Next.js) | Ruff |
| Type Check | TypeScript | Mypy |
| Tests | Vitest | Pytest |
| Coverage | ≥60% functions | ≥70% lines |
| Build | Next.js build | - |

## Exit Codes

- `0` = All checks passed ✅
- `1` = One or more checks failed ❌

## Pro Tips

1. **Run before every push:**
   ```bash
   cd frontend && npm run ci-check && cd .. && git push
   ```

2. **Add to git alias:**
   ```bash
   git config alias.safe-push '!cd frontend && npm run ci-check && cd .. && git push'
   # Then use: git safe-push
   ```

3. **Watch mode during development:**
   ```bash
   npm run test:watch  # Frontend
   make test          # Backend
   ```

4. **Check individual files:**
   ```bash
   npx eslint src/path/to/file.ts  # Frontend
   ruff check src/path/to/file.py  # Backend
   ```

## Troubleshooting

**"Command not found: make"**
```bash
sudo apt-get install make  # Ubuntu/Debian
brew install make          # macOS
```

**"PostgreSQL not running" (backend tests)**
```bash
cd backend
make services-start
```

**Frontend tests timeout**
- Tests can take 30-60 seconds on first run
- Subsequent runs are faster due to caching

**Coverage below threshold**
- Add tests for uncovered code
- Run `npm run test:coverage` to see coverage report
- Check `frontend/coverage/index.html` for detailed report

## Need Help?

See detailed documentation: `scripts/README.md`
