.PHONY: install build test lint format
.DEFAULT_GOAL := help

WORKER_COUNT ?= 4

install:
	poetry install -E parse -E alembic

build:
	poetry build

test:
	SQLALCHEMY_WARN_20=1 \
	COVERAGE_PROCESS_START="$(PWD)/pyproject.toml" \
	coverage run -m pytest -n $(WORKER_COUNT) -vv src tests
	coverage combine
	coverage report -i
	coverage xml

lint:
	ruff check --fix src tests || exit 1
	ruff format -q src tests || exit 1
	mypy src tests || exit 1
	ruff format --check src tests

format:
	ruff check src tests --fix
	ruff format src tests
