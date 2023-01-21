# SQLAlchemy bind manager
[![Python 3.8](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.8.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.8.yml)
[![Python 3.9](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.9.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.9.yml)
[![Python 3.10](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.10.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.10.yml)
[![Python 3.11](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.11.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.11.yml)

[![Maintainability](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/maintainability)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/test_coverage)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/test_coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package provides two functionalities:

* A manager for multiple SQLAlchemy configurations, using typed inputs and decoupled from any framework.
* A generic class implementation to be used in repository pattern

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

🚨 NOTE: Using global variables is not thread-safe, please read the [Threading support](#threading-support) section if your application uses multi-threading.

`engine_url` and `engine_options` dictionary accept the same parameters as SQLAlchemy [create_engine()](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine)

`session_options` dictionary accepts the same parameters as SQLALchemy [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker)

Once the bind manager is initialised we can retrieve and use the SQLAlchemyBind using the method `get_bind()`

The `SQLAlchemyBind` class has the following attributes:

* `bind_async`: A boolean property, `True` when the bind uses an async dialect (Note: async is not yet fully supported, see the section about asynchronous binds)
* `engine`: The initialised SQLALchemy `Engine`
* `model_declarative_base`: A base class that can be used to create [declarative models](https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#declarative-mapping)
* `registry_mapper`: The `registry` associated with the `engine`. It can be used with Alembic or to achieve [imperative mapping](https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#imperative-mapping)
* `session_class`: The class built by [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker), either `Session` or `AsyncSession`

The `SQLAlchemyBindManager` provides some helper methods to quickly access some of the bind properties without using the `SQLAlchemyBind`:

* `get_session`: returns a Session object
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

* `get_session(bind_name="default")`: returns a `Session` or `AsyncSession` object
* `get_mapper(bind_name="default")`: returns the mapper associated with the bind

### Threading

Global variables in python are shared among threads. Neither `SQLAlchemyBindManager` class
or the repositories implementation are thread safe on their own.

If your application uses multi-threads, the same `SQLAlchemyBindManager` object will be
shared between different threads, together with the internal `Session` object,
and changes on models could propagate among them, causing undesired operations.

Make sure you check Python [Threading](https://docs.python.org/3/library/threading.html)
documentation, especially the [Thread-local Data](https://docs.python.org/3/library/threading.html#thread-local-data)
chapter to avoid issues.

### Asynchronous database binds

Is it possible to supply configurations for asyncio supported engines.

```python
config = SQLAlchemyAsyncBindConfig(
    engine_url="postgresql+asyncpg://scott:tiger@localhost/test",
)
```

This will make sure we have an `AsyncEngine` and an `AsyncSession` are initialised.

```python
async with sa_manager.get_session() as session:
    session.add(o)
    session.commit()
```

Note that async implementation has several differences from the sync one, make sure
to check [SQLAlchemy asyncio documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)

## Repository

The `SQLAlchemySyncRepository` and `SQLAlchemyAsyncRepository` class can be used simply by extending them.

```python
from sqlalchemy_bind_manager import SQLAlchemySyncRepository

class MyModel(model_declarative_base):
    pass

class ModelRepository(SQLAlchemySyncRepository[MyModel]):
    _model = MyModel
```

The classes provide some common use methods:

* `get`: Retrieve a model by identifier
* `save`: Persist a model
* `save_many`: Persist multiple models in a single transaction
* `delete`: Delete a model
* `find`: Search for a list of models (basically an adapter for SELECT queries)

### Session lifecycle in repositories

[SQLAlchemy documentation](https://docs.sqlalchemy.org/en/14/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it)
recommends we create `Session` object at the beginning of a logical operation where
database access is potentially anticipated.

Doing this too soon might cause unexpected effects, like unexpected updates being committed,
if the initialised session is shared among different repositories.

A `Repository` represents a generic interface to persist data object to a storage, not necessarily
using SQLAlchemy. It makes sense that the lifecycle of a `Session` follows the one of the Repository
(If we create a Repository, we're going to do a DB operation, otherwise we don't need a `Session`)

This ensures we the `Session` we use is isolated, and the same for all the operations we do with the
repository.

The consequence of this choice is we can't use SQLAlchemy lazy loading, so we need to make sure
relationship are loaded eagerly. You can do this by:

* Setup your model/table relationships to always use always eager loading
* Implement ad-hoc methods to deal with relationships as necessary

Also `AsyncSession` has [the same limitation on lazy loading](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads)
so it makes sense that the two repository implementations behave consistently.
