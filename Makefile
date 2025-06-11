.PHONY: format install run test test-unit test-integration test-cov

format:
	ruff format ./src
	ruff check ./src --fix

install:
	@command -v uv >/dev/null 2>&1 || pip install uv
	uv sync --group test

run:
	uv run -m src.main

run-docker:
	docker compose up -d

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

test-ci:
	uv run pytest --junitxml=junit.xml --cov=src --cov-report=xml

# Health checks and testing commands
test-health:
	uv run pytest tests/integration/test_health_endpoints.py -v --no-cov

health-check:
	@echo "Testing health endpoints..."
	@./scripts/test-health-checks.sh

# Docker build and run
docker-build:
	docker build -t mcp-composer:latest .

docker-run:
	docker run -p 8000:8000 mcp-composer:latest