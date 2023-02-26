.PHONY: build test lint format
.DEFAULT_GOAL := help

WORKER_COUNT ?= 4

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
	ruff src tests
	mypy src tests
	black --check src tests

format:
	black src tests
	ruff src tests --fix
