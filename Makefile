.PHONY: dev-dependencies update-dependencies test docs fix check typing lint format ci-test ci-coverage qlty

#########################
###### dev commands #####
#########################
dev-dependencies:
	uv lock --upgrade
	uv sync --all-groups --frozen

test:
	uv run pytest -n auto --cov

docs:
	uv run mkdocs serve

fix:
	uv run ruff format .
	uv run ruff check . --fix
	uv run ruff format .

qlty:
	qlty smells --all

check:
	uv run tox

typing:
	uv run tox -e typing

lint:
	uv run tox -e lint

format:
	uv run tox -e format


#########################
###### CI commands ######
#########################
ci-test:
	uv run pytest

ci-coverage:
	uv run pytest --cov --cov-report lcov
