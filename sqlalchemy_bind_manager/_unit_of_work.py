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
    Session: scoped_session

    def __init__(self, bind: SQLAlchemyBind):
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        else:
            u = uuid4()
            self.Session = scoped_session(bind.session_class, scopefunc=lambda: str(u))

    def __del__(self):
        if getattr(self, "Session", None):
            self.Session.remove()

    @contextmanager
    def get_session(self, commit: bool = True) -> Iterator[scoped_session]:
        with self.Session() as _session:
            yield _session
            if commit:
                self._commit(_session)

    def _commit(self, session: scoped_session) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: Session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            session.commit()
        except:
            session.rollback()
            raise


class SQLAlchemyAsyncUnitOfWork:
    Session: async_scoped_session

    def __init__(self, bind: SQLAlchemyAsyncBind):
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyAsyncBind")
        else:
            u = uuid4()
            self.Session = async_scoped_session(
                bind.session_class, scopefunc=lambda: str(u)
            )

    def __del__(self):
        if not getattr(self, "Session", None):
            return

        loop = get_event_loop()
        if loop.is_running():
            loop.create_task(self.Session.remove())
        else:
            loop.run_until_complete(self.Session.remove())

    @asynccontextmanager
    async def get_session(
        self, commit: bool = True
    ) -> AsyncIterator[async_scoped_session]:
        async with self.Session() as _session:
            yield _session
            if commit:
                await self._commit(_session)

    async def _commit(self, session: async_scoped_session) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: Session
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            await session.commit()
        except:
            await session.rollback()
            raise
