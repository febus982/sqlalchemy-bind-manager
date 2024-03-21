#  Copyright (c) 2024 Federico Busetti <729029+febus982@users.noreply.github.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

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
from sqlalchemy_bind_manager.exceptions import RepositoryNotFoundError
from sqlalchemy_bind_manager.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyRepository,
)

REPOSITORY = TypeVar("REPOSITORY", SQLAlchemyRepository, SQLAlchemyAsyncRepository)
SESSION_HANDLER = TypeVar("SESSION_HANDLER", SessionHandler, AsyncSessionHandler)


class BaseUnitOfWork(Generic[REPOSITORY, SESSION_HANDLER], ABC):
    _session_handler: SESSION_HANDLER
    _repositories: Dict[str, REPOSITORY]

    def __init__(self):
        self._repositories = {}

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
            raise RepositoryNotFoundError(
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
