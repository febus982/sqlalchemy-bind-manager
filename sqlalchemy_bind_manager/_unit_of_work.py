from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
)
from sqlalchemy.orm import scoped_session

from sqlalchemy_bind_manager import SQLAlchemyBindManager
from sqlalchemy_bind_manager._bind_manager import DEFAULT_BIND_NAME
from sqlalchemy_bind_manager.exceptions import UnsupportedBind


class SAUnitOfWork:
    Session: scoped_session

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = DEFAULT_BIND_NAME
    ):


        bind = sa_manager.get_bind(bind_name)
        if isinstance(bind.engine, AsyncEngine):
            raise UnsupportedBind("AAA")
            # self.Session = async_scoped_session(
            #     bind.session_class, scopefunc=lambda: str(self._scope_id)
            # )
        else:
            u = uuid4()
            self.Session = scoped_session(
                bind.session_class, scopefunc=lambda: str(u)
            )

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
