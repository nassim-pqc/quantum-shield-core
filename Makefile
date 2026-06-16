.DEFAULT_GOAL := help
.PHONY: help install install-dev run test lint fmt sbom docker demo clean

PY ?= python

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	$(PY) -m pip install -r requirements.txt

install-dev: install ## Install runtime + dev dependencies
	$(PY) -m pip install -r requirements-dev.txt

run: ## Run the API locally (reads .env)
	uvicorn main:app --host 0.0.0.0 --port 8000

test: ## Run the test suite
	$(PY) -m pytest -q

lint: ## Lint with ruff
	$(PY) -m ruff check .

fmt: ## Auto-fix lint issues
	$(PY) -m ruff check --fix .

sbom: ## Generate the SBOM
	bash scripts/generate_sbom.sh

docker: ## Build and start the stack
	docker compose up --build

demo: ## Run the end-to-end API demo against a running instance
	bash demo/demo.sh

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
