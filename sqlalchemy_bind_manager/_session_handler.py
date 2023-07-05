import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.orm import Session, scoped_session

from sqlalchemy_bind_manager._bind_manager import (
    SQLAlchemyAsyncBind,
    SQLAlchemyBind,
)
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


class SessionHandler:
    scoped_session: scoped_session

    def __init__(self, bind: SQLAlchemyBind):
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        else:
            self.scoped_session = scoped_session(bind.session_class)

    def __del__(self):
        if getattr(self, "scoped_session", None):
            self.scoped_session.remove()

    @contextmanager
    def get_session(self, read_only: bool = False) -> Iterator[Session]:
        session = self.scoped_session()
        try:
            session.begin()
            yield session
            if not read_only:
                self.commit(session)
        finally:
            session.close()

    def commit(self, session: Session) -> None:
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


class AsyncSessionHandler:
    scoped_session: async_scoped_session

    def __init__(self, bind: SQLAlchemyAsyncBind):
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyAsyncBind")
        else:
            self.scoped_session = async_scoped_session(
                bind.session_class, asyncio.current_task
            )

    def __del__(self):
        if not getattr(self, "scoped_session", None):
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.scoped_session.remove())
            else:
                loop.run_until_complete(self.scoped_session.remove())
        except RuntimeError:
            asyncio.run(self.scoped_session.remove())

    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncIterator[AsyncSession]:
        session = self.scoped_session()
        try:
            await session.begin()
            yield session
            if not read_only:
                await self.commit(session)
        finally:
            await session.close()

    async def commit(self, session: AsyncSession) -> None:
        """Commits the session and handles rollback on errors.

        :param session: The session object.
        :type session: AsyncSession
        :raises Exception: Any error is re-raised after the rollback.
        """
        try:
            await session.commit()
        except:
            await session.rollback()
            raise
