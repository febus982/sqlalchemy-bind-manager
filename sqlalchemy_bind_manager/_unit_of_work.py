from contextlib import contextmanager, asynccontextmanager
from typing import Iterable, Type, Iterator, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from sqlalchemy_bind_manager import SQLAlchemyRepository, SQLAlchemyAsyncRepository
from sqlalchemy_bind_manager._bind_manager import SQLAlchemyBind, SQLAlchemyAsyncBind
from sqlalchemy_bind_manager._transaction_handler import (
    SessionHandler,
    AsyncSessionHandler,
)


class UnitOfWork:
    _transaction_handler: SessionHandler

    def __init__(
        self, bind: SQLAlchemyBind, repositories: Iterable[Type[SQLAlchemyRepository]]
    ) -> None:
        super().__init__()
        self._transaction_handler = SessionHandler(bind)
        for r in repositories:
            setattr(self, r.__name__, r(session=self._transaction_handler.session))

    @contextmanager
    def transaction(self, read_only: bool = False) -> Iterator[Session]:
        with self._transaction_handler.get_session(read_only=read_only) as _s:
            yield _s


class AsyncUnitOfWork:
    _transaction_handler: AsyncSessionHandler

    def __init__(
        self,
        bind: SQLAlchemyAsyncBind,
        repositories: Iterable[Type[SQLAlchemyAsyncRepository]],
    ) -> None:
        super().__init__()
        self._transaction_handler = AsyncSessionHandler(bind)
        for r in repositories:
            setattr(self, r.__name__, r(session=self._transaction_handler.session))

    @asynccontextmanager
    async def transaction(self, read_only: bool = False) -> AsyncIterator[AsyncSession]:
        async with self._transaction_handler.get_session(read_only=read_only) as _s:
            yield _s
