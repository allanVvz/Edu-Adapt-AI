.PHONY: test test-api test-web test-images test-web-health cc lint pre-deploy up down logs

# ─── Tests ─────────────────────────────────────────────────────────────────
test: cc test-api test-web test-web-health
	@echo "\nAll checks passed."

test-api:
	@echo "=== Backend Tests ==="
	docker compose exec -T api python -m pytest tests/ -v --tb=short -q

test-web:
	@echo "=== Frontend Tests (Jest) ==="
	docker compose exec -T web npm test -- --passWithNoTests --watchAll=false

test-images:
	@echo "=== Image Generation Tests (mock DALL-E) ==="
	docker compose exec -T api python -m pytest tests/test_image_generation.py -v --tb=short

test-web-health:
	@echo "=== Frontend HTTP Health Check ==="
	@attempt=1; \
	while [ $$attempt -le 12 ]; do \
		STATUS=$$(docker compose exec -T web node -e \
		  "require('http').get('http://localhost:3000',r=>{process.stdout.write(String(r.statusCode));process.exit(0)}).on('error',()=>process.exit(1))" 2>/dev/null); \
		if [ "$$STATUS" = "200" ]; then \
			echo "Frontend OK — HTTP 200 at localhost:3000"; \
			exit 0; \
		fi; \
		echo "  Not ready (attempt $$attempt/12) — waiting 5s..."; \
		attempt=$$((attempt+1)); \
		sleep 5; \
	done; \
	echo "FAIL: Frontend did not respond with 200 after 60s"; \
	docker compose logs web --tail=20; \
	exit 1

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
