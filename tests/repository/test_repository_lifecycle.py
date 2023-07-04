from unittest.mock import MagicMock

import pytest

from sqlalchemy_bind_manager.exceptions import (
    InvalidConfig,
    InvalidModel,
    UnsupportedBind,
)
from sqlalchemy_bind_manager.repository import SQLAlchemyAsyncRepository


def test_repository_fails_if_not_correct_bind(
    sa_manager, repository_class, model_class
):
    wrong_bind = "sync" if repository_class is SQLAlchemyAsyncRepository else "async"

    with pytest.raises(UnsupportedBind):
        repository_class(bind=sa_manager.get_bind(wrong_bind), model_class=model_class)


def test_repository_fails_if_both_bind_and_session(repository_class, model_class):
    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        repository_class(bind=bind, session=session, model_class=model_class)


def test_repository_fails_if_no_model_or_wrong_model(repository_class, sa_bind):
    class ExtendedClassRepo(repository_class):
        ...

    class SomeObject:
        ...

    with pytest.raises(InvalidModel):
        ExtendedClassRepo(bind=sa_bind)

    with pytest.raises(InvalidModel):
        repository_class(bind=sa_bind)

    with pytest.raises(InvalidModel):
        repository_class(bind=sa_bind, model_class=SomeObject)


def test_repository_initialise_with_valid_model(model_class, repository_class, sa_bind):
    class ExtendedModel(repository_class):
        _model = model_class

    ExtendedModel(bind=sa_bind)
    repository_class(bind=sa_bind, model_class=model_class)
