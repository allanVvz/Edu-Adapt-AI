#!/usr/bin/env bash
# pre-deploy.sh — run before every git push / docker deploy
# Exit on first failure.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() { echo -e "${GREEN}PASS${NC} $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; exit 1; }
step() { echo -e "\n${YELLOW}==> $1${NC}"; }

# ─── 1. Cyclomatic Complexity ────────────────────────────────────────────────
step "Cyclomatic Complexity (radon)"
if command -v radon &>/dev/null; then
  python3 "$ROOT/scripts/check_complexity.py" && pass "CC check"
else
  echo "radon not found — install with: pip install radon==6.0.1"
  echo "Skipping CC check."
fi

# ─── 2. Backend Tests ────────────────────────────────────────────────────────
step "Backend Tests (pytest)"
cd "$ROOT/apps/api"
if python -m pytest tests/ -v --tb=short -q 2>&1; then
  pass "API tests"
else
  fail "API tests — fix failures before deploying"
fi

# ─── 3. Frontend Tests ───────────────────────────────────────────────────────
step "Frontend Tests (jest)"
cd "$ROOT/apps/web"
if npm test -- --passWithNoTests --watchAll=false 2>&1; then
  pass "Frontend tests"
else
  fail "Frontend tests — fix failures before deploying"
fi

# ─── 4. ESLint ───────────────────────────────────────────────────────────────
step "ESLint"
cd "$ROOT/apps/web"
if npm run lint 2>&1; then
  pass "ESLint"
else
  fail "ESLint errors — fix before deploying"
fi

echo -e "\n${GREEN}All checks passed. Ready to deploy.${NC}"
