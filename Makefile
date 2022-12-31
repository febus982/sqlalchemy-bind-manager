test:
	poetry run pytest -n auto --cov

format:
	poetry run black sqlalchemy_bind_manager tests