from abc import ABC
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Dict, Generic, Iterator, Type, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from sqlalchemy_bind_manager._bind_manager import SQLAlchemyAsyncBind, SQLAlchemyBind
from sqlalchemy_bind_manager._session_handler import (
    AsyncSessionHandler,
    SessionHandler,
)
from sqlalchemy_bind_manager.exceptions import RepositoryNotFound
from sqlalchemy_bind_manager.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)

REPOSITORY = TypeVar("REPOSITORY", SQLAlchemyRepository, SQLAlchemyAsyncRepository)
SESSION_HANDLER = TypeVar("SESSION_HANDLER", SessionHandler, AsyncSessionHandler)


class BaseUnitOfWork(Generic[REPOSITORY, SESSION_HANDLER], ABC):
    _session_handler: SESSION_HANDLER
    _repositories: Dict[str, REPOSITORY] = {}

    def register_repository(
        self,
        name: str,
        repository_class: Type[REPOSITORY],
        model_class: Union[Type, None] = None,
        *args,
        **kwargs,
    ):
        kwargs.pop("session", None)
        self._repositories[name] = repository_class(  # type: ignore
            *args,
            session=self._session_handler.scoped_session(),
            model_class=model_class,
            **kwargs,
        )

    def repository(self, name: str) -> REPOSITORY:
        try:
            return self._repositories[name]
        except KeyError:
            raise RepositoryNotFound(
                "The repository has not been initialised in this unit of work"
            )


class UnitOfWork(BaseUnitOfWork[SQLAlchemyRepository, SessionHandler]):
    def __init__(self, bind: SQLAlchemyBind) -> None:
        super().__init__()
        self._session_handler = SessionHandler(bind)

    @contextmanager
    def transaction(self, read_only: bool = False) -> Iterator[Session]:
        with self._session_handler.get_session(read_only=read_only) as _s:
            yield _s


class AsyncUnitOfWork(BaseUnitOfWork[SQLAlchemyAsyncRepository, AsyncSessionHandler]):
    def __init__(
        self,
        bind: SQLAlchemyAsyncBind,
    ) -> None:
        super().__init__()
        self._session_handler = AsyncSessionHandler(bind)

    @asynccontextmanager
    async def transaction(self, read_only: bool = False) -> AsyncIterator[AsyncSession]:
        async with self._session_handler.get_session(read_only=read_only) as _s:
            yield _s
