lint:
	@ruff check .
.PHONY: linter

lint-fix:
	@ruff check . --fix
.PHONY: lint-fix

format-check:
	@autopep8 --diff --recursive . --exclude optimism,op-geth,venv --max-line-length 100 --exit-code
.PHONY: format-check

format:
	@autopep8 --in-place --recursive . --exclude optimism,op-geth,venv --max-line-length 100
.PHONY: format

check: lint format-check
.PHONY: check

fix: lint-fix format
.PHONY: fix
