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
from sqlalchemy_bind_manager.exceptions import UnsupportedBindError


class SessionHandler:
    scoped_session: scoped_session

    def __init__(self, bind: SQLAlchemyBind):
        if not isinstance(bind, SQLAlchemyBind):
            raise UnsupportedBindError("Bind is not an instance of SQLAlchemyBind")
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


# Reference: https://docs.astral.sh/ruff/rules/asyncio-dangling-task/
_background_asyncio_tasks = set()


class AsyncSessionHandler:
    scoped_session: async_scoped_session

    def __init__(self, bind: SQLAlchemyAsyncBind):
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBindError("Bind is not an instance of SQLAlchemyAsyncBind")
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
                task = loop.create_task(self.scoped_session.remove())
                # Add task to the set. This creates a strong reference.
                _background_asyncio_tasks.add(task)

                # To prevent keeping references to finished tasks forever,
                # make each task remove its own reference from the set after
                # completion:
                task.add_done_callback(_background_asyncio_tasks.discard)
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
