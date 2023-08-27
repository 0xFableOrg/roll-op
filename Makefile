linter: ## Run linter
	@ruff check .
.PHONY: linter

check: linter ## Run check
.PHONY: check

format: ## Run format
	@autopep8 --in-place --recursive . --exclude optimism,op-geth,venv --max-line-length 120
.PHONY: format