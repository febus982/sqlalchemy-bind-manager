# SQLAlchemy bind manager
[![Stable Version](https://img.shields.io/pypi/v/sqlalchemy-bind-manager?color=blue)](https://pypi.org/project/sqlalchemy-bind-manager/)
[![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta)

[![Python 3.8](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.8.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.8.yml)
[![Python 3.9](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.9.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.9.yml)
[![Python 3.10](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.10.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.10.yml)
[![Python 3.11](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.11.yml/badge.svg?event=push)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-3.11.yml)

[![Maintainability](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/maintainability)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/test_coverage)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/test_coverage)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

This package provides an easy way to configure and use SQLAlchemy engines and sessions
without depending on frameworks.

It is composed by two main components:

* A manager class for SQLAlchemy engine and session configuration
* A repository/unit-of-work pattern implementation for model retrieval and persistence

## Installation

```bash
pip install sqlalchemy-bind-manager
```

## Components maturity

[//]: # (https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md)
* [![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta) **SQLAlchemy manager:** Implementation is mostly finalised, needs testing in production.
* [![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta) **Repository:** Implementation is mostly finalised, needs testing in production.
* [![stability-experimental](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental) **Unit of work:** The implementation is working but limited to repositories using the same engine. Distributed transactions across different engines are not yet supported.

## Documentation

The complete documentation can be found [here](https://febus982.github.io/sqlalchemy-bind-manager)

## SQLAlchemy manager 

Initialise the manager providing an instance of `SQLAlchemyConfig`

```python
from sqlalchemy_bind_manager import SQLAlchemyConfig, SQLAlchemyBindManager

config = SQLAlchemyConfig(
    engine_url="sqlite:///./sqlite.db",
    engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
    session_options=dict(expire_on_commit=False),
)

sa_manager = SQLAlchemyBindManager(config)
```

🚨 NOTE: Using global variables is not thread-safe, please read the [Documentation](https://febus982.github.io/sqlalchemy-bind-manager/manager/session/#note-on-multithreaded-applications) if your application uses multi-threading.

The `engine_url` and `engine_options` dictionaries accept the same parameters as SQLAlchemy [create_engine()](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine)

The `session_options` dictionary accepts the same parameters as SQLALchemy [sessionmaker()](https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.sessionmaker)

The `SQLAlchemyBindManager` provides some helper methods for common operations:

* `get_bind`: returns a `SQLAlchemyBind` or `SQLAlchemyAsyncBind` object
* `get_session`: returns a `Session` object, which works also as a context manager
* `get_mapper`: returns the mapper associated with the bind

Example:

```python
bind = sa_manager.get_bind()


class MyModel(bind.model_declarative_base):
    pass


# Persist an object
o = MyModel()
o.name = "John"
with sa_manager.get_session() as session:
    session.add(o)
    session.commit()
```

[Imperative model declaration](https://febus982.github.io/sqlalchemy-bind-manager/manager/models/) is also supported.

### Multiple database binds

`SQLAlchemyBindManager` accepts also multiple databases configuration, provided as a dictionary. The dictionary keys are used as a reference name for each bind.

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

* `get_bind(bind_name="default")`: returns a `SQLAlchemyBind` or `SQLAlchemyAsyncBind` object
* `get_session(bind_name="default")`: returns a `Session` or `AsyncSession` object, which works also as a context manager
* `get_mapper(bind_name="default")`: returns the mapper associated with the bind

### Asynchronous database binds

Is it possible to supply configurations for asyncio supported engines.

```python
config = SQLAlchemyAsyncConfig(
    engine_url="postgresql+asyncpg://scott:tiger@localhost/test",
)
```

This will make sure we have an `AsyncEngine` and an `AsyncSession` are initialised, as an asynchronous context manager.

```python
async with sa_manager.get_session() as session:
    session.add(o)
    await session.commit()
```

Note that async implementation has several differences from the sync one, make sure
to check [SQLAlchemy asyncio documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

## Repository / Unit of work

The `SQLAlchemyRepository` and `SQLAlchemyAsyncRepository` class can be used directly or by extending them.

```python
from sqlalchemy_bind_manager.repository import SQLAlchemyRepository


class MyModel(model_declarative_base):
    pass

# Direct usage
repo_instance = SQLAlchemyRepository(sqlalchemy_bind_manager.get_bind(), model_class=MyModel)

class ModelRepository(SQLAlchemyRepository[MyModel]):
    _model = MyModel
    
    def _some_custom_method_implemented(self):
        ...

# Extended class usage
extended_repo_instance = ModelRepository(sqlalchemy_bind_manager.get_bind())
```

The repository classes provides methods for  common use case:

* `get`: Retrieve a model by primary key
* `save`: Persist a model
* `save_many`: Persist multiple models in a single transaction
* `delete`: Delete a model
* `find`: Search for a list of models (basically an adapter for SELECT queries)
* `paginated_find`: Search for a list of models, with pagination support
* `cursor_paginated_find`: Search for a list of models, with cursor based pagination support

### Use the Unit Of Work to share a session among multiple repositories

It is possible we need to run several operations in a single database transaction. While a single
repository provide by itself an isolated session for single operations, we have to use a different
approach for multiple operations.

We can use the `UnitOfWork` or the `AsyncUnitOfWork` class to provide a shared session to
be used for repository operations, **assumed the same bind is used for all the repositories**.

```python
class MyRepo(SQLAlchemyRepository):
    _model = MyModel

bind = sa_manager.get_bind()
uow = UnitOfWork(bind)
uow.register_repository("repo_a", MyRepo)
uow.register_repository("repo_b", SQLAlchemyRepository, MyOtherModel)

with uow.transaction():
    uow.repository("repo_a").save(some_model)
    uow.repository("repo_b").save(some_other_model)
```
