from unittest.mock import MagicMock

import pytest

from sqlalchemy_bind_manager.exceptions import (
    InvalidConfig,
    InvalidModel,
    UnsupportedBind,
)
from sqlalchemy_bind_manager.repository import SQLAlchemyRepository


def test_repository_fails_if_not_sync_bind(sync_async_sa_manager, model_class):
    class SyncRepo(SQLAlchemyRepository):
        _model = model_class

    with pytest.raises(UnsupportedBind):
        SyncRepo(sync_async_sa_manager.get_bind("async"))


def test_repository_fails_if_both_bind_and_session(model_class):
    class SyncRepo(SQLAlchemyRepository):
        _model = model_class

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        SyncRepo(bind, session)


def test_repository_fails_if_no_model_or_wrong_model():
    class AsyncRepo(SQLAlchemyRepository):
        ...

    class SomeObject:
        ...

    with pytest.raises(InvalidModel):
        AsyncRepo()

    with pytest.raises(InvalidModel):
        SQLAlchemyRepository()

    with pytest.raises(InvalidModel):
        SQLAlchemyRepository(model_class=SomeObject)


def test_repository_initialise_with_valid_model(model_class, sa_manager):
    class AsyncRepo(SQLAlchemyRepository):
        _model = model_class

    AsyncRepo(bind=sa_manager.get_bind())
    SQLAlchemyRepository(bind=sa_manager.get_bind(), model_class=model_class)
