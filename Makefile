# Chip Quality Platform
# Production-grade microservices for manufacturing quality inspection

.PHONY: help setup-dev clean test lint format docker-build k8s-deploy

# Colors for pretty output
YELLOW := \033[1;33m
GREEN := \033[1;32m
BLUE := \033[1;34m
RED := \033[1;31m
NC := \033[0m # No Color

# Configuration
PYTHON := python3.11
PIP := pip
DOCKER := docker
KUBECTL := kubectl
HELM := helm
COMPOSE := docker-compose

# Project info
PROJECT_NAME := chip-quality-platform
REGISTRY := ghcr.io/your-org
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "v0.1.0")

help: ## Show this help message
	@echo "$(BLUE)Chip Quality Platform - Makefile Commands$(NC)"
	@echo "================================================"
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(YELLOW)Usage:$(NC)\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Development

setup-dev: ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	$(PYTHON) -m venv venv
	source venv/bin/activate && $(PIP) install --upgrade pip
	source venv/bin/activate && $(PIP) install -r requirements-dev.txt
	pre-commit install
	@echo "$(GREEN)Development environment ready!$(NC)"

dev-gateway: ## Run API Gateway locally
	@echo "$(BLUE)Starting API Gateway...$(NC)"
	cd services/api-gateway && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

dev-inference: ## Run Inference Service locally
	@echo "$(BLUE)Starting Inference Service...$(NC)"
	cd services/inference-svc && python -m app.main

dev-metadata: ## Run Metadata Service locally
	@echo "$(BLUE)Starting Metadata Service...$(NC)"
	cd services/metadata-svc && uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

dev-artifact: ## Run Artifact Service locally
	@echo "$(BLUE)Starting Artifact Service...$(NC)"
	cd services/artifact-svc && uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload

dev-report: ## Run Report Service locally
	@echo "$(BLUE)Starting Report Service...$(NC)"
	cd services/report-svc && python -m app.main

dev-infra: ## Start development infrastructure (Postgres, Kafka, MinIO)
	@echo "$(BLUE)Starting development infrastructure...$(NC)"
	$(COMPOSE) -f compose/docker-compose.dev.yaml up -d postgres kafka zookeeper minio
	@echo "$(GREEN)Infrastructure started!$(NC)"
	@echo "MinIO Console: http://localhost:9001 (admin:admin123)"
	@echo "Kafka UI: http://localhost:8090"

##@ Code Quality

lint: ## Run code linting
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check services/
	mypy services/
	bandit -r services/ -f json -o security-report.json
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format services/
	@echo "$(GREEN)Code formatted!$(NC)"

security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	safety check --json --output security-deps.json
	bandit -r services/ -f json -o security-bandit.json
	trivy fs --format json --output trivy-report.json .
	@echo "$(GREEN)Security scan complete!$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest services/ -v --cov=services --cov-report=html --cov-report=term
	@echo "$(GREEN)All tests passed!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest services/*/tests/unit/ -v

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest services/*/tests/integration/ -v

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	pytest tests/e2e/ -v

test-load: ## Run load tests
	@echo "$(BLUE)Running load tests...$(NC)"
	cd scripts/load && locust -f locustfile.py --headless -u 10 -r 2 -t 60s -H http://localhost:8080

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch services/ --runner="pytest -v"

test-coverage: ## Generate test coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	pytest services/ --cov=services --cov-report=html --cov-report=xml
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

##@ Docker

docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER) build -t $(REGISTRY)/api-gateway:$(VERSION) services/api-gateway/
	$(DOCKER) build -t $(REGISTRY)/ingestion-svc:$(VERSION) services/ingestion-svc/
	$(DOCKER) build -t $(REGISTRY)/inference-svc:$(VERSION) services/inference-svc/
	$(DOCKER) build -t $(REGISTRY)/metadata-svc:$(VERSION) services/metadata-svc/
	$(DOCKER) build -t $(REGISTRY)/artifact-svc:$(VERSION) services/artifact-svc/
	$(DOCKER) build -t $(REGISTRY)/report-svc:$(VERSION) services/report-svc/
	@echo "$(GREEN)Docker images built!$(NC)"

docker-push: ## Push Docker images to registry
	@echo "$(BLUE)Pushing Docker images...$(NC)"
	$(DOCKER) push $(REGISTRY)/api-gateway:$(VERSION)
	$(DOCKER) push $(REGISTRY)/ingestion-svc:$(VERSION)
	$(DOCKER) push $(REGISTRY)/inference-svc:$(VERSION)
	$(DOCKER) push $(REGISTRY)/metadata-svc:$(VERSION)
	$(DOCKER) push $(REGISTRY)/artifact-svc:$(VERSION)
	$(DOCKER) push $(REGISTRY)/report-svc:$(VERSION)
	@echo "$(GREEN)Docker images pushed!$(NC)"

docker-scan: ## Scan Docker images for vulnerabilities
	@echo "$(BLUE)Scanning Docker images...$(NC)"
	trivy image $(REGISTRY)/api-gateway:$(VERSION)
	trivy image $(REGISTRY)/inference-svc:$(VERSION)
	@echo "$(GREEN)Docker scan complete!$(NC)"

##@ Kubernetes

k8s-deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	$(HELM) upgrade --install chip-quality deploy/helm/charts/platform \
		--namespace production --create-namespace \
		--set image.tag=$(VERSION) \
		--values deploy/helm/values/prod.yaml
	@echo "$(GREEN)Deployed to Kubernetes!$(NC)"

k8s-deploy-dev: ## Deploy to development environment
	@echo "$(BLUE)Deploying to development...$(NC)"
	$(HELM) upgrade --install chip-quality-dev deploy/helm/charts/platform \
		--namespace development --create-namespace \
		--set image.tag=$(VERSION) \
		--values deploy/helm/values/dev.yaml
	@echo "$(GREEN)Deployed to development!$(NC)"

k8s-status: ## Check Kubernetes deployment status
	@echo "$(BLUE)Checking deployment status...$(NC)"
	$(KUBECTL) get pods -n production -l app.kubernetes.io/instance=chip-quality
	$(KUBECTL) get svc -n production -l app.kubernetes.io/instance=chip-quality

k8s-logs: ## Tail logs from Kubernetes pods
	@echo "$(BLUE)Tailing logs...$(NC)"
	$(KUBECTL) logs -f -n production -l app.kubernetes.io/name=api-gateway

k8s-port-forward: ## Port forward services for local access
	@echo "$(BLUE)Setting up port forwarding...$(NC)"
	$(KUBECTL) port-forward -n production svc/api-gateway 8080:80 &
	$(KUBECTL) port-forward -n production svc/grafana 3000:80 &
	@echo "$(GREEN)Port forwarding active: API (8080), Grafana (3000)$(NC)"

##@ Database

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd services/metadata-svc && alembic upgrade head
	@echo "$(GREEN)Database migrations complete!$(NC)"

db-reset: ## Reset database (DEV ONLY)
	@echo "$(RED)Resetting database (DEV ONLY)...$(NC)"
	cd services/metadata-svc && alembic downgrade base && alembic upgrade head

db-seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	python scripts/ingest/seed_data.py
	@echo "$(GREEN)Database seeded!$(NC)"

##@ Demo

demo-up: ## Start full demo environment
	@echo "$(BLUE)Starting demo environment...$(NC)"
	$(COMPOSE) -f compose/docker-compose.demo.yaml up -d
	@echo "$(GREEN)Demo environment started!$(NC)"
	@echo "API Gateway: http://localhost:8080/docs"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Grafana: http://localhost:3000"

demo-down: ## Stop demo environment
	@echo "$(BLUE)Stopping demo environment...$(NC)"
	$(COMPOSE) -f compose/docker-compose.demo.yaml down -v

demo-data: ## Load demo data
	@echo "$(BLUE)Loading demo data...$(NC)"
	python scripts/ingest/seed_images.py
	@echo "$(GREEN)Demo data loaded!$(NC)"

demo-test: ## Run demo workflow test
	@echo "$(BLUE)Running demo workflow...$(NC)"
	bash scripts/demo/workflow_test.sh
	@echo "$(GREEN)Demo workflow complete!$(NC)"

##@ Monitoring

monitor-up: ## Start monitoring stack
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	$(COMPOSE) -f compose/docker-compose.monitoring.yaml up -d
	@echo "$(GREEN)Monitoring stack started!$(NC)"
	@echo "Grafana: http://localhost:3000 (admin:admin)"
	@echo "Prometheus: http://localhost:9090"

monitor-down: ## Stop monitoring stack
	@echo "$(BLUE)Stopping monitoring stack...$(NC)"
	$(COMPOSE) -f compose/docker-compose.monitoring.yaml down

##@ Documentation

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	mkdocs build
	@echo "$(GREEN)Documentation built in site/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	mkdocs serve -a 0.0.0.0:8000

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)Deploying documentation...$(NC)"
	mkdocs gh-deploy

##@ Utilities

new-service: ## Create new service template (usage: make new-service name=my-service)
	@echo "$(BLUE)Creating new service: $(name)...$(NC)"
	./scripts/tools/new_service.sh $(name)
	@echo "$(GREEN)Service $(name) created!$(NC)"

gen-openapi: ## Generate OpenAPI documentation
	@echo "$(BLUE)Generating OpenAPI documentation...$(NC)"
	python scripts/tools/gen_openapi_json.py
	@echo "$(GREEN)OpenAPI documentation generated!$(NC)"

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Registry: $(REGISTRY)"

clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -f *.json
	@echo "$(GREEN)Cleanup complete!$(NC)"

##@ CI/CD

ci-test: ## Run CI test suite
	@echo "$(BLUE)Running CI test suite...$(NC)"
	$(MAKE) lint
	$(MAKE) security-scan
	$(MAKE) test
	$(MAKE) docker-build
	$(MAKE) docker-scan
	@echo "$(GREEN)CI tests passed!$(NC)"

release: ## Create a new release
	@echo "$(BLUE)Creating release $(VERSION)...$(NC)"
	git tag -a $(VERSION) -m "Release $(VERSION)"
	git push origin $(VERSION)
	$(MAKE) docker-build
	$(MAKE) docker-push
	@echo "$(GREEN)Release $(VERSION) created!$(NC)"

# Default target
all: lint test docker-build