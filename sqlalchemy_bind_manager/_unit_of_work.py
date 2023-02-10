from asyncio import get_event_loop
from typing import Iterator, AsyncIterator
from contextlib import contextmanager, asynccontextmanager
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    async_scoped_session,
)
from sqlalchemy.orm import scoped_session

from sqlalchemy_bind_manager._bind_manager import (
    SQLAlchemyBind,
    SQLAlchemyAsyncBind,
)
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


class SQLAlchemyUnitOfWork:
    _session: scoped_session

    def __init__(self, bind: SQLAlchemyBind):
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        else:
            u = uuid4()
            self._session = scoped_session(bind.session_class, scopefunc=lambda: str(u))

    def __del__(self):
        if getattr(self, "_session", None):
            self._session.remove()

    @contextmanager
    def get_session(self, commit: bool = True) -> Iterator[scoped_session]:
        with self._session() as _session:
            yield _session
            if commit:
                self._commit(_session)

    def _commit(self, session: scoped_session) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: _session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            session.commit()
        except:
            session.rollback()
            raise


class SQLAlchemyAsyncUnitOfWork:
    _session: async_scoped_session

    def __init__(self, bind: SQLAlchemyAsyncBind):
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyAsyncBind")
        else:
            u = uuid4()
            self._session = async_scoped_session(
                bind.session_class, scopefunc=lambda: str(u)
            )

    def __del__(self):
        if not getattr(self, "_session", None):
            return

        loop = get_event_loop()
        if loop.is_running():
            loop.create_task(self._session.remove())
        else:
            loop.run_until_complete(self._session.remove())

    @asynccontextmanager
    async def get_session(
        self, commit: bool = True
    ) -> AsyncIterator[async_scoped_session]:
        async with self._session() as _session:
            yield _session
            if commit:
                await self._commit(_session)

    async def _commit(self, session: async_scoped_session) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: _session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            await session.commit()
        except:
            await session.rollback()
            raise
