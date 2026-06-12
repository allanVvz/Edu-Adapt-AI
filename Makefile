.PHONY: test test-api test-web cc lint pre-deploy up down logs

# ─── Tests ─────────────────────────────────────────────────────────────────
test: cc test-api test-web
	@echo "\nAll checks passed."

test-api:
	@echo "=== Backend Tests ==="
	docker compose exec -T api python -m pytest tests/ -v --tb=short -q

test-web:
	@echo "=== Frontend Tests ==="
	docker compose exec -T web npm test -- --passWithNoTests --watchAll=false

cc:
	@echo "=== Cyclomatic Complexity ==="
	docker compose exec -T api python -m radon cc /app/app -s -n C --total-average || true

lint:
	docker compose exec -T web npm run lint

# Run tests outside Docker (requires local envs)
test-local-api:
	cd apps/api && python -m pytest tests/ -v --tb=short

test-local-web:
	cd apps/web && npm test -- --passWithNoTests --watchAll=false

# ─── Docker ────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

down-v:
	docker compose down -v

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

restart:
	docker compose restart api web

# ─── Pre-deploy ────────────────────────────────────────────────────────────
pre-deploy:
	@bash scripts/pre-deploy.sh
