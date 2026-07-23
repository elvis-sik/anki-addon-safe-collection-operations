.DEFAULT_GOAL := help

.PHONY: help test lint typecheck build public-scan check clean

help: ## Show available targets.
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: ## Run deterministic unit tests.
	python3 -m unittest discover -s tests -p 'test_*.py' -v

lint: ## Run Ruff when available, then compile every Python file.
	@if command -v ruff >/dev/null 2>&1; then ruff check .; fi
	python3 -m compileall -q __init__.py safe_collection_operations scripts tests

typecheck: ## Run mypy when available.
	@if command -v mypy >/dev/null 2>&1; then mypy safe_collection_operations scripts; fi

build: ## Build the .ankiaddon archive.
	python3 scripts/build_ankiaddon.py

public-scan: ## Reject private paths, hosts, secrets, and generated debris.
	python3 scripts/check_public.py

check: test lint typecheck build public-scan ## Run the full local verification suite.

clean: ## Remove generated build and Python cache output.
	python3 scripts/clean.py

