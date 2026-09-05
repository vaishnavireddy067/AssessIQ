.DEFAULT_GOAL := help

.PHONY: help setup up down logs shell-api shell-db migrate migrate-create test lint format

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup: copy .env and build images
	cp -n .env.example .env || true
	docker compose build

up: ## Start all services
	docker compose up -d

up-logs: ## Start all services and follow logs
	docker compose up

down: ## Stop all services
	docker compose down

down-v: ## Stop all services and remove volumes (DESTROYS DATA)
	docker compose down -v

logs: ## Follow all service logs
	docker compose logs -f

logs-api: ## Follow API logs
	docker compose logs -f api

logs-worker: ## Follow worker logs
	docker compose logs -f worker

shell-api: ## Open a shell inside the API container
	docker compose exec api bash

shell-db: ## Open psql inside the postgres container
	docker compose exec postgres psql -U assessiq_user -d assessiq

migrate: ## Run Alembic migrations
	docker compose exec api alembic upgrade head

migrate-create: ## Create a new Alembic migration (usage: make migrate-create MSG="your message")
	docker compose exec api alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	docker compose exec api alembic history --verbose

test: ## Run backend tests
	docker compose exec api pytest tests/ -v --tb=short

test-cov: ## Run backend tests with coverage
	docker compose exec api pytest tests/ -v --cov=. --cov-report=term-missing

lint: ## Lint backend code
	docker compose exec api ruff check .

format: ## Format backend code
	docker compose exec api ruff format .

seed: ## Seed initial data (roles, super admin, demo company, test users)
	docker compose exec api python scripts/seed_initial_data.py

build-frontend: ## Build frontend for production
	docker compose run --rm frontend npm run build
