.DEFAULT_GOAL := help

SOURCES := src tests docs .github/scripts

.PHONY: help install install-test install-latest lint format typecheck test coverage check \
	docs docs-live docs-clean version build check-release publish clean

help:  ## Show the available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "} {printf "  %-18s %s\n", $$1, $$2}'

install:  ## Create the virtual environment and install all dependencies
	uv sync --locked

install-test:  ## Install the package with what the tests need only
	uv sync --locked --no-default-groups --group test

install-latest:  ## Install what the tests need in its newest versions, ignoring uv.lock
	uv venv --allow-existing
	uv pip install --upgrade --editable . --group test

lint:  ## Check the code style and formatting with ruff
	uv run ruff check $(SOURCES)
	uv run ruff format --check $(SOURCES)

format:  ## Format the code and apply the safe lint fixes
	uv run ruff check --fix $(SOURCES)
	uv run ruff format $(SOURCES)

typecheck:  ## Check the types with mypy
	uv run mypy src tests .github/scripts

test:  ## Run the tests
	uv run pytest

coverage:  ## Run the tests in parallel with a coverage report
	uv run pytest -n auto --cov --cov-report=term-missing:skip-covered --cov-report=xml

check: lint typecheck test docs  ## Run every check that CI runs

docs:  ## Build the HTML documentation, treating warnings as errors
	uv run sphinx-build -b html -W --keep-going docs docs/_build/html

docs-live:  ## Serve the documentation and rebuild it on changes
	uv run sphinx-autobuild docs docs/_build/html

docs-clean:  ## Remove the built and generated documentation
	rm -rf docs/_build docs/reference/api

version:  ## Show the version derived from the git tags
	@uvx --quiet --with hatch-vcs hatchling version

build:  ## Build the source distribution and the wheel
	rm -rf dist
	uv build

check-release:  ## Check that the distributions have the version of a tag: TAG=v1.2.3
	uv run --no-project python .github/scripts/check_release_version.py $(TAG)

publish:  ## Upload the built distributions to PyPI
	uv publish

clean: docs-clean  ## Remove build, test and cache artifacts
	rm -rf dist htmlcov coverage.xml .coverage .pytest_cache .mypy_cache .ruff_cache
