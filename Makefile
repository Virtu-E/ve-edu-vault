# Variables
PYTHON = python
MYPY = mypy
PRECOMMIT = pre-commit

# Default target
.PHONY: all
all: help

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  test          - Run tests using pytest"
	@echo "  type-check    - Run mypy for type checking"
	@echo "  pre-commit    - Run pre-commit hooks on all files"
	@echo "  clean         - Clean up generated files"

# Run tests
.PHONY: test
test:
	pytest


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
