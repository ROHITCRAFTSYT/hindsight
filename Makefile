# Hindsight — common developer tasks.
# On Windows, run these from Git Bash / WSL, or use the underlying commands
# directly (see README). All targets assume you are in the repo root.

.PHONY: help setup backend frontend dev test lint build docker up down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend + frontend dependencies
	cd backend && python -m venv .venv && . .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate; \
		pip install -r requirements-dev.txt
	cd frontend && npm install

backend: ## Run the FastAPI backend on :8000
	cd backend && uvicorn app.main:app --reload --port 8000

frontend: ## Run the Vite dev server on :5173
	cd frontend && npm run dev

test: ## Run backend tests (demo mode, no keys needed)
	cd backend && DEMO_MODE=true python -m pytest

lint: ## Lint the backend with ruff
	cd backend && ruff check app tests

build: ## Production-build the frontend
	cd frontend && npm run build

docker: up ## Alias for `up`

up: ## Start the full stack with Docker (http://localhost:8080)
	docker compose up --build

down: ## Stop the Docker stack
	docker compose down

clean: ## Remove build artifacts and caches
	rm -rf frontend/dist backend/.pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
