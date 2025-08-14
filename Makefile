# Variables
PYTHON = python
PYTEST = $(PYTHON) -m pytest
MYPY = mypy
PRECOMMIT = pre-commit
CELERY = celery
DJANGO_SHELL = $(PYTHON) manage.py shell_plus
UVICORN = uvicorn
DEV_SETTINGS = src.config.django.dev
PROD_SETTINGS = src.config.django.production

# Docker Compose variables - Updated for V2
DOCKER_COMPOSE_BASE = docker compose -f docker-compose.base.yml
DOCKER_COMPOSE_DEV = docker compose -f docker-compose.yml
DOCKER_COMPOSE_PROD = $(DOCKER_COMPOSE_BASE) -f docker-compose.prod.yml

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development Commands:"
	@echo "  test                - Run tests using pytest"
	@echo "                        Command: $(PYTEST)"
	@echo "  test-verbose        - Run tests with verbose output"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -v"
	@echo "  test-quiet          - Run tests with quiet output"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -q"
	@echo "  test-with-coverage  - Run tests with coverage report"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=html"
	@echo "  test-debug          - Run tests with debug information"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -s"
	@echo "  test-specific       - Run a specific test"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -k 'test_name'"
	@echo "  test-file           - Run tests in a specific file"
	@echo "                        Command: $(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing \$(TEST_DIR)/test_file.py"
	@echo "  type-check          - Run mypy for type checking"
	@echo "                        Command: $(MYPY) ."
	@echo "  pre-commit          - Run pre-commit hooks on all files"
	@echo "                        Command: $(PRECOMMIT) run --all-files"
	@echo "  clean               - Clean up generated files"
	@echo "                        Command: find . -name \"__pycache__\" -exec rm -rf {} +; find . -name \"*.pyc\" -exec rm -f {} +"
	@echo "  celery              - Runs a celery worker"
	@echo "                        Command: $(CELERY) -A src.config worker -l info"
	@echo "  shell               - Starts an Ipython shell"
	@echo "                        Command: $(DJANGO_SHELL) --ipython"
	@echo "  serve-async         - Start async server with uvicorn (dev settings)"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(UVICORN) src.config.asgi:application --reload"
	@echo "  serve-async-prod    - Start async server with production settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(UVICORN) src.config.asgi:application"
	@echo "  serve-async-dev     - Start async server with development settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(UVICORN) src.config.asgi:application --reload"
	@echo "  shell-reload        - Starts an Ipython shell with auto-reloading enabled"
	@echo "                        Command: $(DJANGO_SHELL) --ipython"
	@echo "  migrate-dev         - Run database migrations with development settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(PYTHON) manage.py migrate"
	@echo "  migrate-prod        - Run database migrations with production settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(PYTHON) manage.py migrate"
	@echo "  createsuperuser-dev - Create Django superuser with development settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(PYTHON) manage.py createsuperuser"
	@echo "  createsuperuser-prod - Create Django superuser with production settings"
	@echo "                        Command: DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(PYTHON) manage.py createsuperuser"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-dev-up       - Start development environment with Docker"
	@echo "                        Command: $(DOCKER_COMPOSE_DEV) up --build"
	@echo "  docker-dev-up-d     - Start development environment in detached mode"
	@echo "                        Command: $(DOCKER_COMPOSE_DEV) up --build -d"
	@echo "  docker-dev-down     - Stop development environment"
	@echo "                        Command: $(DOCKER_COMPOSE_DEV) down"
	@echo "  docker-prod-up      - Start production environment with Docker"
	@echo "                        Command: $(DOCKER_COMPOSE_PROD) up --build"
	@echo "  docker-prod-up-d    - Start production environment in detached mode"
	@echo "                        Command: $(DOCKER_COMPOSE_PROD) up --build -d"
	@echo "  docker-prod-down    - Stop production environment"
	@echo "                        Command: $(DOCKER_COMPOSE_PROD) down"
	@echo "  docker-rebuild      - Rebuild and restart production environment"
	@echo "                        Command: $(DOCKER_COMPOSE_PROD) down && $(DOCKER_COMPOSE_PROD) up --build --force-recreate"
	@echo "  docker-logs         - Show logs for production environment"
	@echo "                        Command: $(DOCKER_COMPOSE_PROD) logs -f"
	@echo "  docker-clean        - Clean up Docker containers, networks, and volumes"
	@echo "                        Command: docker system prune -f && docker volume prune -f"

.PHONY: shell
shell:
	$(DJANGO_SHELL) --ipython

# Run database migrations with development settings
.PHONY: migrate-dev
migrate-dev:
	DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(PYTHON) manage.py migrate

.PHONY: set-env-dev
set-env-dev:
	@echo "Run this command in your shell:"
	@echo "export DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS)"

.PHONY: set-env-prod
set-env-prod:
	@echo "Run this command in your shell:"
	@echo "export DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS)"

# Run database migrations with production settings
.PHONY: migrate-prod
migrate-prod:
	DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(PYTHON) manage.py migrate

# Create Django superuser with development settings
.PHONY: createsuperuser-dev
createsuperuser-dev:
	DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(PYTHON) manage.py createsuperuser

# Create Django superuser with production settings
.PHONY: createsuperuser-prod
createsuperuser-prod:
	DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(PYTHON) manage.py createsuperuser

# Add a new target for reloadable shell
.PHONY: shell-reload
shell-reload:
	$(DJANGO_SHELL) --ipython

.PHONY: celery
celery:
	$(CELERY) -A src.config worker -l info

# Run async server with uvicorn (defaults to dev settings)
.PHONY: serve-async
serve-async: serve-async-dev

# Run async server with uvicorn using development settings
.PHONY: serve-async-dev
serve-async-dev:
	DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(UVICORN) src.config.asgi:application --host 0.0.0.0 --port 8000 --reload

# Run async server with uvicorn using production settings
.PHONY: serve-async-prod
serve-async-prod:
	DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(UVICORN) src.config.asgi:application

# Run tests with default options
.PHONY: test
test:
	$(PYTEST)

# Run tests with verbose output
.PHONY: test-verbose
test-verbose:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -v

# Run tests with quiet output
.PHONY: test-quiet
test-quiet:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -q

# Run tests with coverage reporting
.PHONY: test-with-coverage
test-with-coverage:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=html

# Run tests with debug information (for print statements)
.PHONY: test-debug
test-debug:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -s

# Run a specific test by name
.PHONY: test-specific
test-specific:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing -k 'test_name'

# Run tests in a specific file
.PHONY: test-file
test-file:
	$(PYTEST) --maxfail=5 --disable-warnings --cov=. --cov-report=term-missing $(TEST_DIR)/test_file.py

# Type checking with mypy
.PHONY: type-check
type-check:
	$(MYPY) .

# Run pre-commit hooks
.PHONY: pre-commit
pre-commit:
	$(PRECOMMIT) run --all-files

# Clean up files
.PHONY: clean
clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +

# Docker Commands
# Development environment
.PHONY: docker-dev-up
docker-dev-up:
	$(DOCKER_COMPOSE_DEV) up --build

.PHONY: docker-dev-up-d
docker-dev-up-d:
	$(DOCKER_COMPOSE_DEV) up --build -d

.PHONY: docker-dev-down
docker-dev-down:
	$(DOCKER_COMPOSE_DEV) down

# Production environment
.PHONY: docker-prod-up
docker-prod-up:
	$(DOCKER_COMPOSE_PROD) up --build

.PHONY: docker-prod-up-d
docker-prod-up-d:
	$(DOCKER_COMPOSE_PROD) up --build -d

.PHONY: docker-prod-down
docker-prod-down:
	$(DOCKER_COMPOSE_PROD) down

# Utility Docker commands
.PHONY: docker-rebuild
docker-rebuild:
	$(DOCKER_COMPOSE_PROD) down
	$(DOCKER_COMPOSE_PROD) up --build --force-recreate

.PHONY: docker-logs
docker-logs:
	$(DOCKER_COMPOSE_PROD) logs -f

.PHONY: docker-clean
docker-clean:
	docker system prune -f
	docker volume prune -f


# Restart development environment
.PHONY: docker-dev-restart
docker-dev-restart:
	$(DOCKER_COMPOSE_DEV) restart

# Restart production environment
.PHONY: docker-prod-restart
docker-prod-restart:
	$(DOCKER_COMPOSE_PROD) restart

# Restart specific service in development environment
.PHONY: docker-dev-restart-service
docker-dev-restart-service:
	$(DOCKER_COMPOSE_DEV) restart $(SERVICE)

# Restart specific service in production environment
.PHONY: docker-prod-restart-service
docker-prod-restart-service:
	$(DOCKER_COMPOSE_PROD) restart $(SERVICE)

# Quick restart development (down + up without rebuild)
.PHONY: docker-dev-quick-restart
docker-dev-quick-restart:
	$(DOCKER_COMPOSE_DEV) down
	$(DOCKER_COMPOSE_DEV) up -d

# Quick restart production (down + up without rebuild)
.PHONY: docker-prod-quick-restart
docker-prod-quick-restart:
	$(DOCKER_COMPOSE_PROD) down
	$(DOCKER_COMPOSE_PROD) up -d


.PHONY: docker-dev-rebuild-web
docker-dev-rebuild-web:
	$(DOCKER_COMPOSE_DEV) build web
	$(DOCKER_COMPOSE_DEV) up -d web

.PHONY: docker-prod-rebuild-web
docker-prod-rebuild-web:
	$(DOCKER_COMPOSE_PROD) build web
	$(DOCKER_COMPOSE_PROD) up -d web
