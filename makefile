.PHONY: test coverage coverage-no-report format lint init install-dev install-fixtures install-datasets install-geodata reset-db
.ONESHELL:
SHELL := /bin/bash
SHELLFLAGS := -ec

# Run all tests with pytest
test:
	pytest --asyncio-mode=auto

# Run tests with coverage
coverage:
	pytest --cov=. --cov-report=term-missing --cov-report=html

# Run tests with coverage without report
coverage-no-report:
	pytest --cov=. --cov-report=term-missing
	
# Format code with Black and isort
format:
	black . && isort .

# Lint code with Flake8
lint:
	flake8 .

# Install dependencies
init:
	uv pip --system install -r pyproject.toml

# Install dev
install-dev:
	python cli/cli.py core loaddev $(filter-out $@,$(MAKECMDGOALS))

install-fixtures:
	python cli/cli.py core loadfixtures dev

install-datasets:
	python cli/cli.py core loaddatasets

install-geodata:
	python cli/cli.py core loadgeodata
	
# Reset database
reset-db:
	python cli/cli.py core resetdb

# Allow running `make install-dev` without arguments
%:
	@true