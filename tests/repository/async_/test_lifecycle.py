from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from sqlalchemy_bind_manager import SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager.exceptions import (
    UnsupportedBind,
    InvalidConfig,
    InvalidModel,
)


def test_repository_fails_if_not_async_bind(sync_async_sa_manager, model_class):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        _model = model_class
        Session = None

    with pytest.raises(UnsupportedBind):
        AsyncRepo(sync_async_sa_manager.get_bind("sync"))


def test_repository_fails_if_both_bind_and_session(model_class):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        _model = model_class

    bind = MagicMock()
    session = MagicMock()
    with pytest.raises(InvalidConfig):
        AsyncRepo(bind, session)


def test_repository_fails_if_no_model_or_wrong_model():
    class AsyncRepo(SQLAlchemyAsyncRepository):
        ...

    class SomeObject:
        ...

    with pytest.raises(InvalidModel):
        AsyncRepo()

    with pytest.raises(InvalidModel):
        SQLAlchemyAsyncRepository()

    with pytest.raises(InvalidModel):
        SQLAlchemyAsyncRepository(model_class=SomeObject)


def test_repository_initialise_with_valid_model(model_class, sa_manager):
    class AsyncRepo(SQLAlchemyAsyncRepository):
        _model = model_class

    r = AsyncRepo(bind=sa_manager.get_bind())
    r2 = SQLAlchemyAsyncRepository(bind=sa_manager.get_bind(), model_class=model_class)
