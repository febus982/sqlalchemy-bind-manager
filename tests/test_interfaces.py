from inspect import signature
from typing import Protocol, runtime_checkable

from sqlalchemy_bind_manager.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyAsyncRepositoryInterface,
    SQLAlchemyRepository,
    SQLAlchemyRepositoryInterface,
)


@runtime_checkable
class RuntimeRepoProtocol(SQLAlchemyRepositoryInterface, Protocol): ...


@runtime_checkable
class RuntimeAsyncRepoProtocol(SQLAlchemyAsyncRepositoryInterface, Protocol): ...


def test_interfaces():
    assert issubclass(SQLAlchemyRepository, RuntimeRepoProtocol)
    assert issubclass(SQLAlchemyAsyncRepository, RuntimeAsyncRepoProtocol)

    sync_methods = [
        method
        for method in dir(SQLAlchemyRepositoryInterface)
        if method.startswith("_") is False
    ]
    async_methods = [
        method
        for method in dir(SQLAlchemyAsyncRepositoryInterface)
        if method.startswith("_") is False
    ]

    assert sync_methods == async_methods

    for method in sync_methods:
        # Concrete sync signature is the same as sync protocol signature
        assert signature(getattr(SQLAlchemyRepository, method)) == signature(
            getattr(SQLAlchemyRepositoryInterface, method)
        )
        # Concrete async signature is the same as async protocol signature
        assert signature(getattr(SQLAlchemyAsyncRepository, method)) == signature(
            getattr(SQLAlchemyAsyncRepositoryInterface, method)
        )
        # Sync protocol signature is the same as async protocol signature
        assert signature(
            getattr(SQLAlchemyAsyncRepositoryInterface, method)
        ) == signature(getattr(SQLAlchemyRepositoryInterface, method))
