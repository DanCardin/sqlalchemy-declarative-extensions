.PHONY: build test lint format
.DEFAULT_GOAL := help

build:
	poetry build

test:
	coverage run -a -m py.test src tests
	coverage report
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
