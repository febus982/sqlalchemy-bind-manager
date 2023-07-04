from typing import Type, Union

import pytest

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind, SQLAlchemyBind
from sqlalchemy_bind_manager._repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)
from sqlalchemy_bind_manager.repository import AsyncUnitOfWork, UnitOfWork


@pytest.fixture
def uow_class(sa_bind):
    return AsyncUnitOfWork if isinstance(sa_bind, SQLAlchemyAsyncBind) else UnitOfWork


@pytest.fixture
def repository_class(
    sa_bind: Union[SQLAlchemyBind, SQLAlchemyAsyncBind]
) -> Type[Union[SQLAlchemyAsyncRepository, SQLAlchemyRepository]]:
    base_class = (
        SQLAlchemyRepository
        if isinstance(sa_bind, SQLAlchemyBind)
        else SQLAlchemyAsyncRepository
    )

    return base_class
