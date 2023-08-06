
linter: ## Run linter
	@ruff check .
.PHONY: linter

check: linter ## Run check
.PHONY: check