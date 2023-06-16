from abc import ABC
from contextlib import contextmanager
from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Tuple,
    Type,
    Union,
)

from sqlalchemy.orm import Session

from .._bind_manager import SQLAlchemyBind
from .._transaction_handler import SessionHandler
from ..exceptions import InvalidConfig, ModelNotFound
from .common import (
    MODEL,
    PRIMARY_KEY,
    BaseRepository,
    CursorPaginatedResult,
    PaginatedResult,
    SortDirection,
)


class SQLAlchemyRepository(Generic[MODEL], BaseRepository[MODEL], ABC):
    _session_handler: SessionHandler
    _external_session: Union[Session, None]

    def __init__(
        self,
        bind: Union[SQLAlchemyBind, None] = None,
        session: Union[Session, None] = None,
        model_class: Union[Type[MODEL], None] = None,
    ) -> None:
        """
        :param bind: A configured instance of SQLAlchemyBind
        :type bind: Union[SQLAlchemyBind, None]
        :param session: An externally managed session
        :type session: Union[Session, None]
        :param model_class: A mapped SQLAlchemy model
        :type model_class: Union[Type[MODEL], None]
        """
        super().__init__(model_class=model_class)
        if not (bool(bind) ^ bool(session)):
            raise InvalidConfig("Either `bind` or `session` have to be used, not both")
        self._external_session = session
        if bind:
            self._session_handler = SessionHandler(bind)

    @contextmanager
    def _get_session(self, commit: bool = True) -> Iterator[Session]:
        if not self._external_session:
            with self._session_handler.get_session(not commit) as _session:
                yield _session
        else:
            yield self._external_session

    def save(self, instance: MODEL) -> MODEL:
        """Persist a model.

        :param instance: A mapped object instance to be persisted
        :return: The model instance after being persisted
        """
        with self._get_session() as session:
            session.add(instance)
        return instance

    def save_many(self, instances: Iterable[MODEL]) -> Iterable[MODEL]:
        """Persist many models in a single database get_session.

        :param instances: A list of mapped objects to be persisted
        :type instances: Iterable
        :return: The model instances after being persisted
        """
        with self._get_session() as session:
            session.add_all(instances)
        return instances

    def get(self, identifier: PRIMARY_KEY) -> MODEL:
        """Get a model by primary key.

        :param identifier: The primary key
        :return: A model instance
        :raises ModelNotFound: No model has been found using the primary key
        """
        # TODO: implement get_many()
        with self._get_session(commit=False) as session:
            model = session.get(self._model, identifier)
        if model is None:
            raise ModelNotFound("No rows found for provided primary key.")
        return model

    def delete(self, entity: Union[MODEL, PRIMARY_KEY]) -> None:
        """Deletes a model.

        :param entity: The model instance or the primary key
        :type entity: Union[MODEL, PRIMARY_KEY]
        """
        # TODO: delete without loading the model
        if isinstance(entity, self._model):
            obj = entity
        else:
            obj = self.get(entity)  # type: ignore
        with self._get_session() as session:
            session.delete(obj)

    def find(
        self,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> List[MODEL]:
        """Find models using filters

        E.g.
        find(name="John") finds all models with name = John

        :param search_params: A dictionary containing equality filters
        :param order_by:
        :return: A collection of models
        :rtype: List
        """
        stmt = self._find_query(search_params, order_by)

        with self._get_session() as session:
            result = session.execute(stmt)
            return [x for x in result.scalars()]

    def paginated_find(
        self,
        items_per_page: int,
        page: int,
        search_params: Union[None, Mapping[str, Any]] = None,
        order_by: Union[None, Iterable[Union[str, Tuple[str, SortDirection]]]] = None,
    ) -> PaginatedResult[MODEL]:
        """Find models using filters and page based pagination

        E.g.
        find(name="John") finds all models with name = John

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param page: Page to retrieve
        :type page: int
        :param search_params: A dictionary containing equality filters
        :param order_by:
        :return: A collection of models
        :rtype: List
        """

        find_stmt = self._find_query(search_params, order_by)
        paginated_stmt = self._paginate_query_by_page(find_stmt, page, items_per_page)

        with self._get_session() as session:
            total_items_count = (
                session.execute(self._count_query(find_stmt)).scalar() or 0
            )
            result_items = [x for x in session.execute(paginated_stmt).scalars()]

            return self._build_page_based_paginated_result(
                result_items=result_items,
                total_items_count=total_items_count,
                page=page,
                items_per_page=items_per_page,
            )

    def cursor_paginated_find(
        self,
        items_per_page: int,
        order_by: str,
        before: Union[int, str, None] = None,
        after: Union[int, str, None] = None,
        search_params: Union[None, Mapping[str, Any]] = None,
    ) -> CursorPaginatedResult[MODEL]:
        """Find models using filters and cursor based pagination

        E.g.
        find(name="John") finds all models with name = John

        :param items_per_page: Number of models to retrieve
        :type items_per_page: int
        :param order_by: Model property to use for ordering and before/after evaluation
        :type order_by: str
        :param before: Identifier of the last node to skip
        :type before: Union[int, str]
        :param after: Identifier of the last node to skip
        :type after: Union[int, str]
        :param search_params: A dictionary containing equality filters
        :return: A collection of models
        :rtype: List
        """

        find_stmt = self._find_query(search_params)
        paginated_stmt = self._cursor_paginated_query(
            find_stmt,
            order_column=order_by,
            before=before,
            after=after,
            per_page=items_per_page,
        )

        with self._get_session() as session:
            total_items_count = (
                session.execute(self._count_query(find_stmt)).scalar() or 0
            )
            result_items = [x for x in session.execute(paginated_stmt).scalars()]
            sanitised_query_limit = self._calculate_sanitised_query_limit(
                items_per_page
            )

            if len(result_items) > sanitised_query_limit:
                has_next_page = True
                result_items = result_items[0:sanitised_query_limit]
            else:
                has_next_page = False

            previous_page_cursor_reference = (
                getattr(result_items[0], order_by) if result_items else after or before
            )
            previous_page_stmt = self._cursor_paginated_query(
                find_stmt,
                order_column=order_by,
                before=previous_page_cursor_reference if before is None else None,
                after=previous_page_cursor_reference if after is None else None,
                per_page=1,
            )

            has_previous_page = bool(
                session.execute(self._count_query(previous_page_stmt)).scalar() or 0
            )

            if before is not None:
                result_items.reverse()

            return CursorPaginatedResult(
                items=result_items,
                items_per_page=sanitised_query_limit,
                total_items=total_items_count,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
            )
