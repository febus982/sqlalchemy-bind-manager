.PHONY: docs docs-build

test:
	poetry run pytest -n auto --cov

ci-test:
	poetry run pytest

ci-coverage:
	poetry run pytest --cov --cov-report lcov

typing:
	poetry run mypy

format:
	poetry run black --check .

lint:
	poetry run ruff .

format-fix:
	poetry run black .

lint-fix:
	poetry run ruff . --fix

dev-dependencies:
	poetry update --with dev

fix:  format-fix lint-fix
check: typing test format lint

docs:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build
