# SQLAlchemy bind manager

This package provides an easy way to configure and use SQLAlchemy without
depending on frameworks.

It is composed by two main components:

* A manager class for SQLAlchemy engine and session configuration
* A repository/unit-of-work pattern implementation for model retrieval and persistence

## Why another SQLAlchemy helper package?

There are some existing plugins that help the creation of the standard SQLAlchemy boilerplate
code for engine, session and base declarative model, but they mainly aim to integrate
with existing frameworks.

In order to create a maintainable application it is important to use a framework, but to
not be limited by it. It might be desirable to switch to more modern technologies
and binding the storage layer with the framework would bring a high degree of complexity.

Also implementing a highly decoupled application would use abstractions between the application 
logic and the storage, therefore this package provides a base implementation of a storage
abstraction layer (Repository).

The scope of this package is to:

* Be able to setup a basic application with a few lines of code
* Avoid common pitfalls found in other plugins for session lifecycle
* Allow to build a [decoupled application](https://github.com/febus982/bootstrap-python-fastapi) without being bound to HTTP frameworks

## Components maturity

The components have a high test coverage, and it should not be necessary to change the interfaces,
however this might be necessary until version `1.0` is released.

[//]: # (https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md)
* [![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta) **SQLAlchemy manager:** Implementation is mostly finalised, needs testing in production.
* [![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta) **Repository:** Implementation is mostly finalised, needs testing in production.
* [![stability-experimental](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental) **Unit of work:** The implementation is working but limited to repositories using the same engine. Distributed transactions across different engines are not yet supported.

## Installation

```bash
pip install sqlalchemy-bind-manager
```

## Quick start

```python
from sqlalchemy_bind_manager import SQLAlchemyConfig, SQLAlchemyBindManager
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

config = SQLAlchemyConfig(
    engine_url="sqlite:///./sqlite.db",
    engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
    session_options=dict(expire_on_commit=False),
)

# Initialise the bind manager
sa_manager = SQLAlchemyBindManager(config)

# Declare a model
class MyModel(sa_manager.get_bind().declarative_base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

# Initialise the tables in the db
bind = sa_manager.get_bind()
bind.registry_mapper.metadata.create_all(bind.engine)

# Create and save a model
o = MyModel()
o.name = "John"
with sa_manager.get_session() as session:
    session.add(o)
    session.commit()
```

/// details | Long lived sessions and multithreading
    type: warning

It's not recommended to create long-lived sessions like:

```
session = sa_manager.get_session()
```

This can create unexpected because of global variables and multi-threading.
More details can be found in the [session page](manager/session/#note-on-multithreaded-applications)
///
