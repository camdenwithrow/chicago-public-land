CONTAINER_ENGINE ?= podman
COMPOSE ?= $(CONTAINER_ENGINE) compose

.PHONY: install db-up db-down dev-api dev-web ingest score lint format typecheck test check

install:
	uv sync --all-groups
	cd apps/web && bun install --frozen-lockfile

db-up:
	$(COMPOSE) up -d db

db-down:
	$(COMPOSE) down

dev-api:
	uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && bun run dev

ingest:
	uv run python -m pipeline ingest

score:
	uv run python -m pipeline score

lint:
	uv run ruff check .
	cd apps/web && bun run lint

format:
	uv run ruff format .
	cd apps/web && bun run format

typecheck:
	uv run mypy apps pipeline
	cd apps/web && bun run typecheck

test:
	uv run pytest

check: lint typecheck test
	cd apps/web && bun run build
