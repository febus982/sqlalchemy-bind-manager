from inspect import signature

from sqlalchemy_bind_manager.protocols import (
    SQLAlchemyAsyncRepositoryProtocol,
    SQLAlchemyRepositoryProtocol,
)
from sqlalchemy_bind_manager.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)


def test_protocols():
    assert issubclass(SQLAlchemyRepository, SQLAlchemyRepositoryProtocol)
    assert issubclass(SQLAlchemyAsyncRepository, SQLAlchemyAsyncRepositoryProtocol)

    sync_methods = [
        method
        for method in dir(SQLAlchemyRepositoryProtocol)
        if method.startswith("_") is False
    ]
    async_methods = [
        method
        for method in dir(SQLAlchemyAsyncRepositoryProtocol)
        if method.startswith("_") is False
    ]

    assert sync_methods == async_methods

    for method in sync_methods:
        # Sync signature is the same as sync protocol
        assert signature(getattr(SQLAlchemyRepository, method)) == signature(
            getattr(SQLAlchemyRepositoryProtocol, method)
        )
        # Async signature is the same as async protocol
        assert signature(getattr(SQLAlchemyAsyncRepository, method)) == signature(
            getattr(SQLAlchemyRepositoryProtocol, method)
        )
        # Sync signature is the same as async signature
        assert signature(
            getattr(SQLAlchemyAsyncRepositoryProtocol, method)
        ) == signature(getattr(SQLAlchemyRepositoryProtocol, method))
