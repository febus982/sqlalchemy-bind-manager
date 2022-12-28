# SQLAlchemy bind manager
[![Maintainability](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/maintainability)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/maintainability)
<a href="https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/test_coverage"><img src="https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/test_coverage" /></a>

A package to manage SQLAlchemy binds, using typed configuration and independent by any framework.


## Usage

Initialise the manager providing an instance of `SQLAlchemyBindConfig`

```python
from sqlalchemy_bind_manager import SQLAlchemyBindConfig, SQLAlchemyBindManager

config = SQLAlchemyBindConfig(
    engine_url="sqlite:///./sqlite.db",
    engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
    session_options=dict(expire_on_commit=False),
)

sa_manager = SQLAlchemyBindManager(config)
```

`engine_url` and `engine_options` dictionary accept the same parameters as SQLAlchemy [create_engine()](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine)

`session_options` dictionary accepts the same parameters as SQLALchemy [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker)

Once the bind manager is initialised we can retrieve and use the SQLAlchemyBind using the method `get_bind()`

The `SQLAlchemyBind` class has the following attributes:

* `bind_async`: A boolean property, `True` when the bind uses an async dialect (Note: async is not yet fully supported, see the section about asynchronous binds)
* `engine`: The initialised SQLALchemy `Engine`
* `model_declarative_base`: A base class that can be used to create (declarative models)[https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping]
* `registry_mapper`: The `registry` associated with the `engine`. It can be used with Alembic or to achieve (imperative mapping)[https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#imperative-mapping]
* `session_class`: The class built by [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker), either `Session` or `AsyncSession`

The `SQLAlchemyBindManager` provides some helper methods to quickly access some of the bind properties without using the `SQLAlchemyBind`:

* `get_session`: returns a Session object
* `get_async_session`: returns an AsyncSession object (Note: async is not yet fully supported, see the section about asynchronous binds)
* `get_mapper`: returns the mapper associated with the bind

Example:

```python
bind = sa_manager.get_bind()

class DeclarativeModel(bind.model_declarative_base):
    pass
    
class ImperativeModel:
    id: int

imperative_table = Table(
    "imperative",
    bind.registry_mapper.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, primary_key=True),
)

bind.registry_mapper.map_imperatively(ImperativeModel, imperative_table)

# or using the get_mapper() helper method
sa_manager.get_mapper().map_imperatively(ImperativeModel, imperative_table)

# Persist an object
o = ImperativeModel() # also o = DeclarativeModel()
o.name = "John"
with sa_manager.get_bind().session_class()() as session:
    session.add(o)
    session.commit()

# or using the get_session() helper method for better readability
with sa_manager.get_session() as session:
    session.add(o)
    session.commit()

```

### Multiple database binds

`SQLAlchemyBindManager` accepts also multiple databases configuration, provided as a dictionary. The dictionary keys are used as a reference name for each bind.

```python
from sqlalchemy_bind_manager import SQLAlchemyBindConfig, SQLAlchemyBindManager

config = {
    "default": SQLAlchemyBindConfig(
        engine_url="sqlite:///./sqlite.db",
        engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
        session_options=dict(expire_on_commit=False),
    ),
    "secondary": SQLAlchemyBindConfig(
        engine_url="sqlite:///./secondary.db",
        engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
        session_options=dict(expire_on_commit=False),
    ),
}

sa_manager = SQLAlchemyBindManager(config)
```

All the `SQLAlchemyBindManager` helper methods accept the `bind_name` optional parameter:

* `get_session(bind_name="default")`: returns a Session object
* `get_async_session(bind_name="default")`: returns an AsyncSession object (Note: async is not yet fully supported, see the section about asynchronous binds)
* `get_mapper(bind_name="default")`: returns the mapper associated with the bind

### Asynchronous database binds [DEV]

**DISCLAIMER:** The support for async binds is still in development and its interfaces might be subject to changes.

Is it possible to supply configurations for asyncio supported engines.

```python
config = SQLAlchemyBindConfig(
    engine_url="postgresql+asyncpg://scott:tiger@localhost/test",
    engine_async=True,
)
```

This will create the engine as `AsyncEngine`, while you will be able to use the `get_async_session` method to get an `AsyncSession`

```python
async with sa_manager.get_async_session() as session:
    session.add(o)
    session.commit()
```

Refer to (SQLAlchemy asyncio documentation)[https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html]
