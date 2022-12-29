test:
	poetry run pytest --cov

format:
	poetry run black sqlalchemy_bind_manager tests