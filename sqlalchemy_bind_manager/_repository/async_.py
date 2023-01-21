from abc import ABC
from typing import Union, Generic, Iterable, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .._bind_manager import (
    SQLAlchemyBindManager,
    DEFAULT_BIND_NAME,
    SQLAlchemyAsyncBind,
)
from ..exceptions import (
    ModelNotFound,
    UnsupportedBind,
)
from .common import MODEL, PRIMARY_KEY, SortDirection, BaseRepository


class SQLAlchemyAsyncRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _session: AsyncSession

    def __init__(
        self, sa_manager: SQLAlchemyBindManager, bind_name: str = DEFAULT_BIND_NAME
    ) -> None:
        """

        :param sa_manager: A configured instance of SQLAlchemyBindManager
        :type sa_manager: SQLAlchemyBindManager
        :param bind_name: The name of the bind as defined in the SQLAlchemyConfig. defaults to "default"
        """
        super().__init__()
        bind = sa_manager.get_bind(bind_name)
        if not isinstance(bind, SQLAlchemyAsyncBind):
            raise UnsupportedBind("Bind is not an instance of SQLAlchemyBind")
        self._session = bind.session_class()

    def __del__(self):
        self._session.close()

    async def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted (e.g. with primary key populated)
        """
        async with self._session as session:  # type: ignore
            session.add(instance)
            await self._commit(session)
        return instance

    async def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database transaction.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted (e.g. with primary keys populated)
        """
        async with self._session as session:  # type: ignore
            session.add_all(instances)
            await self._commit(session)
        return instances

    async def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        model = await self._session.get(self._model, identifier)  # type: ignore
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    async def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        """
        # TODO: delete without loading the model
        obj = entity if self._is_mapped_object(entity) else await self.get(entity)  # type: ignore
        async with self._session as session:  # type: ignore
            await session.delete(obj)
            await self._commit(session)

    async def find(
        self,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
        **search_params,
    ) -> Iterable[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param order_by:
        :param search_params: Any keyword argument to be used as equality filter
        :return: A collection of models
        :rtype: Iterable
        """
        stmt = select(self._model)  # type: ignore
        stmt = self._filter_select(stmt, **search_params)

        if order_by is not None:
            stmt = self._filter_order_by(stmt, order_by)

        async with self._session as session:  # type: ignore
            result = await session.execute(stmt)
            for model_obj in result.scalars():
                yield model_obj

    async def _commit(self, session: AsyncSession) -> None:
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
