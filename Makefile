.PHONY: install run format lint test check

install:
	uv sync --all-groups

run:
	uv run uvicorn commerce_search.main:app --reload

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test:
	uv run pytest --cov --cov-report=term-missing

check: lint test
