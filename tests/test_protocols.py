from inspect import signature

from sqlalchemy_bind_manager import SQLAlchemyRepository, SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager.protocols import SQLAlchemyRepositoryInterface, SQLAlchemyAsyncRepositoryInterface


def test_protocols():
    assert issubclass(SQLAlchemyRepository, SQLAlchemyRepositoryInterface)
    assert issubclass(SQLAlchemyAsyncRepository, SQLAlchemyAsyncRepositoryInterface)

    sync_methods = [method for method in dir(SQLAlchemyRepositoryInterface) if method.startswith('_') is False]
    async_methods = [method for method in dir(SQLAlchemyAsyncRepositoryInterface) if method.startswith('_') is False]

    assert sync_methods == async_methods

    for method in sync_methods:
        # Sync signature is the same as sync protocol
        assert signature(getattr(SQLAlchemyRepository, method)) == signature(getattr(SQLAlchemyRepositoryInterface, method))
        # Async signature is the same as async protocol
        assert signature(getattr(SQLAlchemyAsyncRepository, method)) == signature(getattr(SQLAlchemyRepositoryInterface, method))
        # Sync signature is the same as async signature
        assert signature(getattr(SQLAlchemyAsyncRepositoryInterface, method)) == signature(getattr(SQLAlchemyRepositoryInterface, method))
