lint:
	@ruff check .
.PHONY: linter

lint-fix:
	@ruff check . --fix
.PHONY: lint-fix

AUTOPEP8_EXCLUDES=optimism,op-geth,venv,account-abstraction
AUTOPEP8_OPTIONS=--recursive . --exclude $(AUTOPEP8_EXCLUDES) --max-line-length 100

format-check:
	@autopep8 --diff --exit-code $(AUTOPEP8_OPTIONS)
.PHONY: format-check

format:
	@autopep8 --in-place $(AUTOPEP8_OPTIONS)
.PHONY: format

check: lint format-check
.PHONY: check

fix: lint-fix format
.PHONY: fix
