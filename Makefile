.PHONY: build test lint format
.DEFAULT_GOAL := help

WORKER_COUNT ?= 4

build:
	poetry build

test:
	COVERAGE_PROCESS_START="$(PWD)/pyproject.toml" coverage run -m pytest -n $(WORKER_COUNT) -vv src tests
	coverage combine
	coverage report -i
	coverage xml

lint:
	ruff src tests
	mypy src tests
	black --check src tests

format:
	ruff src tests --fix
	black src tests
