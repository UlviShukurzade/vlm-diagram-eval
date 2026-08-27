.PHONY: help setup parser parser-stop test test-fast lint format clean

IMAGE   := mermaid-parser-service
CONTAINER := mermaid-parser-instance
PORT    := 9595

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup:  ## Install dependencies into a local venv
	uv sync --all-extras
	uv run pre-commit install

parser:  ## Build and start the Mermaid parser service on :$(PORT)
	docker build -t $(IMAGE) services/mermaid_parser
	-docker rm -f $(CONTAINER) 2>/dev/null
	docker run -d -p $(PORT):8000 --name $(CONTAINER) --restart unless-stopped $(IMAGE)
	@echo "Parser service listening on http://localhost:$(PORT)"

parser-stop:  ## Stop and remove the parser service
	-docker rm -f $(CONTAINER)

test:  ## Run the full test suite (needs `make parser`)
	uv run pytest

test-fast:  ## Run only tests that do not need the parser service
	uv run pytest -m "not needs_parser"

lint:  ## Lint and type-check
	uv run ruff check .
	uv run mypy src

format:  ## Auto-format
	uv run ruff format .
	uv run ruff check --fix .

clean:  ## Remove caches and build artefacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist htmlcov .coverage
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
