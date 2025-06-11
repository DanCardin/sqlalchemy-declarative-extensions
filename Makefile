.PHONY: install test lint format
.DEFAULT_GOAL := help

WORKER_COUNT ?= 4

install:
	uv sync --all-extras

test:
	SQLALCHEMY_WARN_20=1 \
	COVERAGE_PROCESS_START="$(PWD)/pyproject.toml" \
	uv run \
	coverage run -m pytest -n $(WORKER_COUNT) -vv src tests
	uv run coverage combine
	uv run coverage report -i
	uv run coverage xml

lint:
	uv run ruff check --fix src tests || exit 1
	uv run ruff format -q src tests || exit 1
	uv run mypy src tests || exit 1
	uv run ruff format --check src tests

format:
	uv run ruff check src tests --fix
	uv run ruff format src tests
