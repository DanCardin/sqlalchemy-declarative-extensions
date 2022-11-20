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
	flake8 --ignore=E203,W503 src tests
	isort --check-only src tests
	pydocstyle src tests
	mypy src tests
	black --check src tests

format:
	isort src tests
	black src tests
