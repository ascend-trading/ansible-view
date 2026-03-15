VENV      := .venv
PYTHON    := python3
PIP       := $(VENV)/bin/pip
PYTEST    := $(VENV)/bin/pytest
RUFF      := $(VENV)/bin/ruff
MYPY      := $(VENV)/bin/mypy

.PHONY: setup dev test lint format typecheck check clean help

## setup  – create venv and install runtime dependencies only
setup: $(VENV)/bin/ansible-view

$(VENV)/bin/ansible-view:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet -e .
	@echo ""
	@echo "Done. Run:  source $(VENV)/bin/activate && ansible-view <playbook.yml>"
	@echo "Or:         ./bin/ansible-view <playbook.yml>"

## dev    – create venv and install all development dependencies
dev: $(VENV)/bin/pytest

$(VENV)/bin/pytest: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet -e ".[dev]"
	@echo "Dev environment ready."

## test   – run the test suite with coverage
test: dev
	$(PYTEST) tests/ -v --cov=src/ansible_view --cov-report=term-missing

## lint   – check code style and imports
lint: dev
	$(RUFF) check src/ tests/

## format – auto-format source files
format: dev
	$(RUFF) format src/ tests/

## typecheck – run mypy type checking
typecheck: dev
	$(MYPY) src/ansible_view

## check  – run lint + typecheck + tests (full CI check)
check: lint typecheck test

## clean  – remove the virtual environment and cache files
clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +

## help   – show this message
help:
	@grep -E '^## ' Makefile | sed 's/## /  make /'
