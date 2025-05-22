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

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available targets:"
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

.PHONY: shell
shell:
	$(DJANGO_SHELL) --ipython

# Run database migrations with development settings
.PHONY: migrate-dev
migrate-dev:
	DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(PYTHON) manage.py migrate

# Run database migrations with production settings
.PHONY: migrate-prod
migrate-prod:
	DJANGO_SETTINGS_MODULE=$(PROD_SETTINGS) $(PYTHON) manage.py migrate

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
	DJANGO_SETTINGS_MODULE=$(DEV_SETTINGS) $(UVICORN) src.config.asgi:application --reload

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
