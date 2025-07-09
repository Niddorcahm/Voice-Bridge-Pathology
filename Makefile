# Voice Bridge Pathology - Makefile
# Automation for common development and deployment tasks

.PHONY: help install test lint format clean build deploy dev-setup docs security backup

# Default target
help: ## Show this help message
	@echo "Voice Bridge Pathology - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# Development Environment Setup
# ==========================================

install: ## Install Voice Bridge Pathology with all dependencies
	@echo "Installing Voice Bridge Pathology..."
	./install.sh

dev-setup: ## Setup development environment
	@echo "Setting up development environment..."
	@if command -v uv &> /dev/null; then \
		uv venv .venv; \
		. .venv/bin/activate; \
		uv pip install -r requirements.txt; \
		uv pip install pytest pytest-cov black isort flake8 mypy bandit safety; \
	else \
		python3 -m venv .venv; \
		. .venv/bin/activate; \
		pip install --upgrade pip; \
		pip install -r requirements.txt; \
		pip install pytest pytest-cov black isort flake8 mypy bandit safety; \
	fi
	@echo "Development environment ready!"

env-template: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "Created .env file from template. Please edit with your settings."; \
	else \
		echo ".env file already exists."; \
	fi

# ==========================================
# Code Quality and Testing
# ==========================================

test: ## Run all tests
	@echo "Running test suite..."
	@. .venv/bin/activate && pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@. .venv/bin/activate && pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires Azure credentials)
	@echo "Running integration tests..."
	@. .venv/bin/activate && pytest tests/integration/ -v -m integration

test-medical: ## Run medical-specific tests
	@echo "Running medical tests..."
	@. .venv/bin/activate && pytest tests/ -v -m medical

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@. .venv/bin/activate && pytest tests/ --cov=voice_bridge_app --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	@echo "Running linting checks..."
	@. .venv/bin/activate && flake8 voice_bridge_app.py
	@. .venv/bin/activate && mypy voice_bridge_app.py --ignore-missing-imports

format: ## Format code with black and isort
	@echo "Formatting code..."
	@. .venv/bin/activate && black voice_bridge_app.py
	@. .venv/bin/activate && isort voice_bridge_app.py

format-check: ## Check code formatting without making changes
	@echo "Checking code formatting..."
	@. .venv/bin/activate && black --check voice_bridge_app.py
	@. .venv/bin/activate && isort --check-only voice_bridge_app.py

security: ## Run security scans
	@echo "Running security scans..."
	@. .venv/bin/activate && bandit -r voice_bridge_app.py
	@. .venv/bin/activate && safety check

quality: lint format-check security test ## Run all quality checks

# ==========================================
# Documentation
# ==========================================

docs: ## Build documentation
	@echo "Building documentation..."
	@if [ -d docs ]; then \
		. .venv/bin/activate && sphinx-build -b html docs docs/_build/html; \
		echo "Documentation built in docs/_build/html/"; \
	else \
		echo "No docs directory found. Creating basic structure..."; \
		mkdir -p docs; \
		echo "Please setup Sphinx documentation first."; \
	fi

docs-serve: ## Serve documentation locally
	@echo "Serving documentation at http://localhost:8000"
	@python3 -m http.server 8000 --directory docs/_build/html

# ==========================================
# Docker Operations
# ==========================================

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t voice-bridge-pathology:latest .

docker-run: ## Run Voice Bridge in Docker container
	@echo "Running Voice Bridge in Docker..."
	docker-compose up voice-bridge-pathology

docker-dev: ## Run development environment in Docker
	@echo "Starting development environment..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

docker-prod: ## Run production environment with all services
	@echo "Starting production environment..."
	docker-compose --profile web --profile database up -d

docker-stop: ## Stop all Docker containers
	@echo "Stopping Docker containers..."
	docker-compose down

docker-clean: ## Remove Docker containers and images
	@echo "Cleaning Docker resources..."
	docker-compose down --rmi all --volumes --remove-orphans

# ==========================================
# Configuration and Maintenance
# ==========================================

config-validate: ## Validate configuration files
	@echo "Validating configuration..."
	@if [ -f examples/validate_config.sh ]; then \
		chmod +x examples/validate_config.sh; \
		./examples/validate_config.sh; \
	else \
		echo "Configuration validation script not found."; \
	fi

config-backup: ## Backup configuration and medical dictionaries
	@echo "Creating configuration backup..."
	@if [ -f examples/backup_config.sh ]; then \
		chmod +x examples/backup_config.sh; \
		./examples/backup_config.sh; \
	else \
		echo "Backup script not found."; \
	fi

azure-test: ## Test Azure Speech Services connectivity
	@echo "Testing Azure connectivity..."
	@if [ -f test_azure_connection.sh ]; then \
		chmod +x test_azure_connection.sh; \
		./test_azure_connection.sh; \
	else \
		echo "Azure test script not found."; \
	fi

# ==========================================
# Medical Dictionary Management
# ==========================================

dict-add: ## Add medical term to dictionary (usage: make dict-add TERM="new term" CATEGORY=patologia_molecular)
	@if [ -z "$(TERM)" ]; then \
		echo "Usage: make dict-add TERM=\"medical term\" [CATEGORY=patologia_molecular]"; \
		exit 1; \
	fi
	@CATEGORY=$${CATEGORY:-patologia_molecular}; \
	if [ -f scripts/add_medical_term.sh ]; then \
		chmod +x scripts/add_medical_term.sh; \
		./scripts/add_medical_term.sh "$(TERM)" "$$CATEGORY"; \
	else \
		echo "Medical term addition script not found."; \
	fi

dict-stats: ## Show medical dictionary statistics
	@echo "Medical Dictionary Statistics:"
	@echo "=============================="
	@if [ -d config/diccionarios ]; then \
		for dict in config/diccionarios/*.txt; do \
			if [ -f "$$dict" ]; then \
				name=$$(basename "$$dict" .txt); \
				count=$$(grep -v '^#' "$$dict" | grep -v '^$$' | wc -l); \
				echo "$$name: $$count terms"; \
			fi; \
		done; \
	else \
		echo "Medical dictionaries directory not found."; \
	fi

# ==========================================
# Deployment and Release
# ==========================================

build: ## Build distribution packages
	@echo "Building distribution packages..."
	@. .venv/bin/activate && python -m build

release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	@make quality
	@make config-validate
	@make azure-test
	@echo "Release checks completed!"

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	@echo "Staging deployment not implemented yet."

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	@echo "Production deployment not implemented yet."

# ==========================================
# Cleanup and Maintenance
# ==========================================

clean: ## Clean build artifacts and cache files
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-logs: ## Clean old log files (keeps last 7 days)
	@echo "Cleaning old log files..."
	@if [ -d logs ]; then \
		find logs/ -name "*.log" -mtime +7 -delete; \
		echo "Old log files cleaned."; \
	else \
		echo "No logs directory found."; \
	fi

clean-all: clean clean-logs docker-clean ## Clean everything including Docker resources

# ==========================================
# System Requirements Check
# ==========================================

check-deps: ## Check system dependencies
	@echo "Checking system dependencies..."
	@echo "Python version:"
	@python3 --version
	@echo ""
	@echo "Required system tools:"
	@command -v wmctrl >/dev/null && echo "✓ wmctrl found" || echo "✗ wmctrl missing"
	@command -v xdotool >/dev/null && echo "✓ xdotool found" || echo "✗ xdotool missing"
	@command -v curl >/dev/null && echo "✓ curl found" || echo "✗ curl missing"
	@echo ""
	@echo "Audio system:"
	@if [ -e /dev/snd ]; then echo "✓ Audio devices found"; else echo "✗ No audio devices"; fi

check-permissions: ## Check file permissions
	@echo "Checking file permissions..."
	@ls -la voice_bridge_app.py
	@if [ -d config ]; then ls -la config/; fi
	@if [ -d logs ]; then ls -la logs/; fi

# ==========================================
# Development Utilities
# ==========================================

dev-start: ## Start development environment
	@echo "Starting development environment..."
	@. .venv/bin/activate && python voice_bridge_app.py

dev-debug: ## Start in debug mode
	@echo "Starting in debug mode..."
	@export DEBUG_MODE=true && . .venv/bin/activate && python voice_bridge_app.py

monitor-logs: ## Monitor application logs in real-time
	@if [ -d logs ]; then \
		tail -f logs/voice_bridge_*.log; \
	else \
		echo "No logs directory found."; \
	fi

# ==========================================
# Git and Version Control
# ==========================================

git-setup: ## Setup git hooks and configuration
	@echo "Setting up git configuration..."
	@git config --local core.autocrlf false
	@git config --local core.eol lf
	@echo "Git configuration completed."

version: ## Show current version
	@grep -E "version.*=" pyproject.toml | head -1 | cut -d'"' -f2

# ==========================================
# Help and Information
# ==========================================

info: ## Show system and project information
	@echo "Voice Bridge Pathology - System Information"
	@echo "=========================================="
	@echo "Project Version: $$(make version)"
	@echo "Python Version: $$(python3 --version)"
	@echo "Operating System: $$(uname -s) $$(uname -r)"
	@echo "Current User: $$(whoami)"
	@echo "Working Directory: $$(pwd)"
	@echo ""
	@echo "Environment Variables:"
	@echo "AZURE_SPEECH_KEY: $${AZURE_SPEECH_KEY:+Set (hidden)}"
	@echo "AZURE_SPEECH_REGION: $${AZURE_SPEECH_REGION:-Not set}"
	@echo ""

status: ## Show project status
	@echo "Voice Bridge Pathology - Project Status"
	@echo "======================================"
	@echo "Installation: $$([ -f voice_bridge_app.py ] && echo 'Complete' || echo 'Incomplete')"
	@echo "Virtual Environment: $$([ -d .venv ] && echo 'Present' || echo 'Missing')"
	@echo "Configuration: $$([ -f config/voice_bridge_config.ini ] && echo 'Present' || echo 'Missing')"
	@echo "Medical Dictionaries: $$([ -d config/diccionarios ] && echo 'Present' || echo 'Missing')"
	@echo "Docker: $$(command -v docker >/dev/null && echo 'Available' || echo 'Not available')"

# ==========================================
# Advanced Features
# ==========================================

benchmark: ## Run performance benchmarks
	@echo "Running performance benchmarks..."
	@echo "Benchmark functionality not implemented yet."

profile: ## Profile application performance
	@echo "Profiling application performance..."
	@echo "Profiling functionality not implemented yet."

# Default values for variables
TERM ?= ""
CATEGORY ?= patologia_molecular

# Ensure scripts are executable
.PHONY: make-scripts-executable
make-scripts-executable:
	@find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
	@find examples/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Include make-scripts-executable in relevant targets
install: make-scripts-executable
dev-setup: make-scripts-executable
