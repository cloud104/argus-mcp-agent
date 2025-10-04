# Makefile for Argus Agent

.PHONY: help build dev prod test clean docker-build docker-push k8s-deploy helm-install

# Variables
DOCKER_REGISTRY ?= southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops
API_IMAGE ?= argus-api
MCP_IMAGE ?= argus-mcp-server
UI_IMAGE ?= argus-ui
VERSION ?= latest
TIMESTAMP := $(shell date +%Y%m%d-%H%M%S)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev: ## Run application in development mode with docker-compose
	docker-compose up

dev-build: ## Build and run development environment
	docker-compose up --build

dev-debug: ## Run with debugging enabled
	docker-compose -f docker-compose.dev.yml up

dev-down: ## Stop development environment
	docker-compose down

dev-logs: ## View development logs
	docker-compose logs -f

# Production Docker - Build and Push locally
docker-login: ## Login to GCP Artifact Registry
	gcloud auth configure-docker southamerica-east1-docker.pkg.dev

docker-build: ## Build production Docker images (api + mcp-server + ui)
	@echo "🔨 Building API image..."
	docker build -f api/Dockerfile -t $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION) ./api
	@echo "🔨 Building MCP Server image..."
	docker build -f mcp-server/Dockerfile -t $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION) ./mcp-server
	@echo "🔨 Building UI image..."
	docker build -f ui/Dockerfile -t $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION) ./ui
	@echo "✅ Images built successfully!"
	@echo ""
	@echo "Images created:"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION)"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION)"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION)"

docker-build-dev: ## Build development Docker images
	docker build -f api/Dockerfile.dev -t argus-api:dev ./api
	docker build -f mcp-server/Dockerfile.dev -t argus-mcp-server:dev ./mcp-server
	docker build -f ui/Dockerfile.dev -t argus-ui:dev ./ui

docker-push: ## Push Docker images to GCP Artifact Registry
	@echo "📤 Pushing API image..."
	docker push $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION)
	@echo "📤 Pushing MCP Server image..."
	docker push $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION)
	@echo "📤 Pushing UI image..."
	docker push $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION)
	@echo "✅ Images pushed successfully!"
	@echo ""
	@echo "Images available at:"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION)"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION)"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION)"

docker-build-push: docker-build docker-push ## Build and push images in one command

docker-build-timestamp: ## Build with timestamp tag (YYYYMMDD-HHMMSS)
	@echo "🔨 Building with timestamp: $(TIMESTAMP)"
	docker build -f api/Dockerfile -t $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP) ./api
	docker build -f mcp-server/Dockerfile -t $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP) ./mcp-server
	docker build -f ui/Dockerfile -t $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP) ./ui
	@echo "✅ Images built with timestamp!"
	@echo ""
	@echo "Images created:"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP)"

docker-push-timestamp: ## Push images with timestamp tag
	@echo "📤 Pushing images with timestamp: $(TIMESTAMP)"
	docker push $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP)
	docker push $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP)
	docker push $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP)
	@echo "✅ Images pushed successfully!"

docker-build-push-timestamp: docker-build-timestamp docker-push-timestamp ## Build and push with timestamp in one command

docker-build-dual: ## Build with both latest and timestamp tags
	@echo "🔨 Building with tags: latest and $(TIMESTAMP)"
	docker build -f api/Dockerfile \
		-t $(DOCKER_REGISTRY)/$(API_IMAGE):latest \
		-t $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP) ./api
	docker build -f mcp-server/Dockerfile \
		-t $(DOCKER_REGISTRY)/$(MCP_IMAGE):latest \
		-t $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP) ./mcp-server
	docker build -f ui/Dockerfile \
		-t $(DOCKER_REGISTRY)/$(UI_IMAGE):latest \
		-t $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP) ./ui
	@echo "✅ Images built with dual tags!"
	@echo ""
	@echo "Images created:"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP)"

docker-push-dual: ## Push both latest and timestamp tags
	@echo "📤 Pushing images with dual tags..."
	docker push $(DOCKER_REGISTRY)/$(API_IMAGE):latest
	docker push $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP)
	docker push $(DOCKER_REGISTRY)/$(MCP_IMAGE):latest
	docker push $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP)
	docker push $(DOCKER_REGISTRY)/$(UI_IMAGE):latest
	docker push $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP)
	@echo "✅ All images pushed successfully!"

docker-release: docker-login docker-build-dual docker-push-dual ## Complete release: login + build + push (latest + timestamp)
	@echo ""
	@echo "🎉 Release complete!"
	@echo ""
	@echo "Images available at:"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(API_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(TIMESTAMP)"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):latest"
	@echo "  - $(DOCKER_REGISTRY)/$(UI_IMAGE):$(TIMESTAMP)"

docker-tag: ## Tag images with custom version (usage: make docker-tag VERSION=v1.0.0)
	docker tag $(DOCKER_REGISTRY)/$(API_IMAGE):latest $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION)
	docker tag $(DOCKER_REGISTRY)/$(MCP_IMAGE):latest $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION)
	docker tag $(DOCKER_REGISTRY)/$(UI_IMAGE):latest $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION)

docker-pull: ## Pull images from registry
	docker pull $(DOCKER_REGISTRY)/$(API_IMAGE):$(VERSION)
	docker pull $(DOCKER_REGISTRY)/$(MCP_IMAGE):$(VERSION)
	docker pull $(DOCKER_REGISTRY)/$(UI_IMAGE):$(VERSION)

# Kubernetes - Development
k8s-dev-deploy: ## Deploy to Kubernetes development environment
	kubectl apply -f k8s/dev/namespace.yaml
	kubectl apply -f k8s/dev/pvc.yaml
	kubectl apply -f k8s/dev/

k8s-dev-delete: ## Delete Kubernetes development deployment
	kubectl delete -f k8s/dev/

k8s-dev-logs: ## View Kubernetes development logs
	kubectl logs -n argus-dev -l app=argus-api --tail=100 -f

k8s-dev-port-forward: ## Port forward to development deployment
	kubectl port-forward -n argus-dev svc/argus-api 8000:8000

create-k8s-secret: ## Create Kubernetes secret from .env file (development)
	@echo "Creating Kubernetes secret in argus-dev namespace from .env..."
	@if [ ! -f .env ]; then echo "Error: .env file not found"; exit 1; fi
	@kubectl create namespace argus-dev --dry-run=client -o yaml | kubectl apply -f -
	@set -a && . ./.env && set +a && \
	kubectl create secret generic argus-secrets \
		--namespace=argus-dev \
		--from-literal=OPENAI_API_KEY="$${OPENAI_API_KEY}" \
		--from-literal=GOOGLE_API_KEY="$${GOOGLE_API_KEY}" \
		--from-literal=ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" \
		--from-literal=ES_HOST="$${ES_HOST}" \
		--from-literal=ES_USER="$${ES_USER}" \
		--from-literal=ES_PASSWORD="$${ES_PASSWORD}" \
		--dry-run=client -o yaml | kubectl apply -f -

create-k8s-configmap: ## Create Kubernetes configmap from config files (development)
	@echo "Creating Kubernetes configmap in argus-dev namespace..."
	@kubectl create namespace argus-dev --dry-run=client -o yaml | kubectl apply -f -
	@kubectl create configmap argus-settings \
		--namespace=argus-dev \
		--from-file=config/settings.json \
		--from-file=config/models.json \
		--dry-run=client -o yaml | kubectl apply -f -

generate-k8s-secret: ## Generate Kubernetes secret.yaml from .env (DO NOT COMMIT!)
	@./scripts/generate-k8s-secret.sh

# Helm
helm-lint: ## Lint Helm chart
	helm lint ./helm/argus-agent

helm-template: ## Generate Kubernetes manifests from Helm chart
	helm template argus ./helm/argus-agent --values k8s/dev/values.yaml

helm-install-dev: ## Install Helm chart in development
	helm install argus-dev ./helm/argus-agent \
		--namespace argus-dev \
		--create-namespace \
		--values k8s/dev/values.yaml

helm-upgrade-dev: ## Upgrade Helm chart in development
	helm upgrade argus-dev ./helm/argus-agent \
		--namespace argus-dev \
		--values k8s/dev/values.yaml

helm-uninstall-dev: ## Uninstall Helm chart from development
	helm uninstall argus-dev --namespace argus-dev

helm-install-prod: ## Install Helm chart in production
	helm install argus-prod ./helm/argus-agent \
		--namespace argus-production \
		--create-namespace \
		--values k8s/prod/values.yaml \
		--set image.tag=$(VERSION)

helm-upgrade-prod: ## Upgrade Helm chart in production
	helm upgrade argus-prod ./helm/argus-agent \
		--namespace argus-production \
		--values k8s/prod/values.yaml \
		--set image.tag=$(VERSION)

# Tilt
tilt-up: ## Start Tilt development environment
	tilt up

tilt-down: ## Stop Tilt development environment
	tilt down

tilt-ci: ## Run Tilt in CI mode
	tilt ci

# Testing
test: ## Run tests
	docker-compose run --rm api pytest -v

test-cov: ## Run tests with coverage
	docker-compose run --rm api pytest --cov=app --cov-report=html

lint: ## Run linting
	docker-compose run --rm api ruff check .

format: ## Format code
	docker-compose run --rm api black .

type-check: ## Run type checking
	docker-compose run --rm api mypy .

# Cleanup
clean: ## Clean up build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

clean-docker: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

# Setup
setup: ## Initial setup (copy .env.example, create venv)
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ Created .env from .env.example"; else echo "⚠️  .env already exists, skipping"; fi
	@if [ ! -d .venv ]; then python3 -m venv .venv; echo "✅ Created virtual environment"; else echo "⚠️  .venv already exists, skipping"; fi
	@echo ""
	@echo "📝 Next steps:"
	@echo "  1. Edit .env with your API keys and credentials"
	@echo "  2. Activate venv: source .venv/bin/activate"
	@echo "  3. Install deps: pip install -r requirements.txt"
