.PHONY: help build run dev test lint format clean install

help:
	@echo "Available targets:"
	@echo "  install - Install dependencies with uv"
	@echo "  build   - Build Docker image"
	@echo "  run     - Run visualization generation in Docker"
	@echo "  dev     - Run locally with uv"
	@echo "  test    - Run tests"
	@echo "  lint    - Run linter"
	@echo "  format  - Format code with ruff"
	@echo "  clean   - Remove output files and caches"

install:
	uv sync

build:
	docker compose build

run:
	docker compose run --rm abwasser

dev:
	uv run python -m abwasser -v

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	rm -rf output/*
	rm -rf .pytest_cache
	rm -rf src/**/__pycache__
	rm -rf tests/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
