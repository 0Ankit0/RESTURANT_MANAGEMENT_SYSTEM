copy-env:
	./scripts/copy_env_templates.sh

setup:
	./scripts/setup_template.sh

docs:
	python3 scripts/validate_documentation.py

docs-check: docs

backend-lint:
	cd backend && uv run ruff check src tests

backend-test:
	cd backend && uv run pytest

backend-dev:
	cd backend && uv run task start

backend-migrate:
	cd backend && uv run task migrate

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm run typecheck && npm run test && npm run build

frontend-dev:
	cd frontend && npm run dev

mobile-lint:
	cd mobile && flutter analyze

mobile-test:
	cd mobile && flutter test

mobile-dev:
	cd mobile && flutter run

dev-up:
	docker compose up --build

infra-up:
	docker compose up -d db redis

dev-down:
	docker compose down -v

infra-down:
	docker compose down -v

health-check:
	python3 scripts/check_template_health.py

lint: backend-lint frontend-lint mobile-lint

test: backend-test frontend-test mobile-test

dev:
	@echo "Run services in separate terminals:"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"
	@echo "  make mobile-dev"

ci: docs lint test
