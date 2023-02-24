from asyncio import get_event_loop
from typing import Iterator, AsyncIterator
from contextlib import contextmanager, asynccontextmanager
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    async_scoped_session,
    AsyncSession,
)
from sqlalchemy.orm import scoped_session, Session

from sqlalchemy_bind_manager._bind_manager import (
    SQLAlchemyBind,
    SQLAlchemyAsyncBind,
)
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


class SessionHandler:
    _session_class: scoped_session
    session: Session

    def __init__(self, bind: SQLAlchemyBind):
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        else:
            u = uuid4()
            self._session_class = scoped_session(
                bind.session_class, scopefunc=lambda: str(u)
            )
            self.session = self._session_class()

    def __del__(self):
        if getattr(self, "_session_class", None):
            self._session_class.remove()

    @contextmanager
    def get_session(self, read_only: bool = False) -> Iterator[Session]:
        try:
            self.session.begin()
            yield self.session
            if not read_only:
                self.commit()
        finally:
            self.session.close()

    def commit(self) -> None:
        """Commits the session and handles rollback on errors.

        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise


class AsyncSessionHandler:
    _session_class: async_scoped_session
    session: AsyncSession

    def __init__(self, bind: SQLAlchemyAsyncBind):
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyAsyncBind")
        else:
            u = uuid4()
            self._session_class = async_scoped_session(
                bind.session_class, scopefunc=lambda: str(u)
            )
            self.session = self._session_class()

    def __del__(self):
        if not getattr(self, "_session_class", None):
            return

        loop = get_event_loop()
        if loop.is_running():
            loop.create_task(self._session_class.remove())
        else:
            loop.run_until_complete(self._session_class.remove())

    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncIterator[AsyncSession]:
        try:
            await self.session.begin()
            yield self.session
            if not read_only:
                await self.commit()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: Session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            await self.session.commit()
        except:
            await self.session.rollback()
            raise
