## Single database configuration

You can initialise the manager providing an instance of `SQLAlchemyConfig`

```python
from sqlalchemy_bind_manager import SQLAlchemyConfig, SQLAlchemyBindManager

config = SQLAlchemyConfig(
    engine_url="sqlite:///./sqlite.db",
    engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
    session_options=dict(expire_on_commit=False),
)

sa_manager = SQLAlchemyBindManager(config)
```

The `engine_url` and `engine_options` dictionaries accept the same parameters as SQLAlchemy [create_engine()](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine)

The `session_options` dictionary accepts the same parameters as SQLALchemy [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker)

Once the bind manager is initialised we can retrieve and use the SQLAlchemyBind using the method `get_bind()`

The `SQLAlchemyBind` class has the following attributes:

* `engine`: The initialised SQLALchemy `Engine`
* `model_declarative_base`: A base class that can be used to create [declarative models](https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping)
* `registry_mapper`: The `registry` associated with the `engine`. It can be used with Alembic or to setup [imperative mapping](https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#imperative-mapping)
* `session_class`: The class built by [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker), either `Session` or `AsyncSession`

The `SQLAlchemyBindManager` provides some helper methods to quickly access some of the bind properties without using the `SQLAlchemyBind`:

* `get_session`: returns a Session object
* `get_mapper`: returns the mapper associated with the bind

## Multiple databases configuration

`SQLAlchemyBindManager` accepts also multiple databases configuration, provided as a dictionary.
The dictionary keys are used as a reference name for each bind.

```python
from sqlalchemy_bind_manager import SQLAlchemyConfig, SQLAlchemyBindManager

config = {
    "default": SQLAlchemyConfig(
        engine_url="sqlite:///./sqlite.db",
        engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
        session_options=dict(expire_on_commit=False),
    ),
    "secondary": SQLAlchemyConfig(
        engine_url="sqlite:///./secondary.db",
        engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
        session_options=dict(expire_on_commit=False),
    ),
}

sa_manager = SQLAlchemyBindManager(config)
```

All the `SQLAlchemyBindManager` helper methods accept the `bind_name` optional parameter:

* `get_session(bind_name="default")`
* `get_mapper(bind_name="default")`

## Asynchronous database engines

Is it possible to supply configurations for asyncio supported engines using `SQLAlchemyAsyncConfig` objects.

```python
from sqlalchemy_bind_manager import SQLAlchemyAsyncConfig, SQLAlchemyBindManager

config = SQLAlchemyAsyncConfig(
    engine_url="postgresql+asyncpg://scott:tiger@localhost/test",
)

sa_manager = SQLAlchemyBindManager(config)
```

This will make sure we initialise a `SQLAlchemyAsyncBind` object, containing `AsyncEngine` and `AsyncSession`.

The interfaces are exactly the same, however you'll need to `await` the relevant functions in SQLAlchemy. E.g.:

```python
async with sa_manager.get_session() as session:
    session.add(o)
    session.commit()
```

Note that async implementation has several differences from the sync one, make sure
to check [SQLAlchemy asyncio documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
