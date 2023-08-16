install:
	curl -sSL https://install.python-poetry.org | python3 -
	poetry config virtualenvs.in-project true
	poetry install

lint:
	poetry run black ./*.py
	poetry run isort ./*.py
