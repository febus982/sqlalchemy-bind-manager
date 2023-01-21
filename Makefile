test:
	poetry run pytest -n auto --cov
	poetry run mypy

format:
	poetry run black sqlalchemy_bind_manager tests
