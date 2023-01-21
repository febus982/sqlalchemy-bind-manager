test: mypy
	poetry run pytest -n auto --cov

mypy:
	poetry run mypy

format:
	poetry run black sqlalchemy_bind_manager tests
