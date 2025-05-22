.PHONY: test coverage format lint

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
install:
	uv pip install -r pyproject.toml


# Install dev
install-dev:
	python cli/cli.py core loadallfixtures dev

# Reset database
reset-db:
	python cli/cli.py core resetdb