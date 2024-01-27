# SQLAlchemy bind manager
![Static Badge](https://img.shields.io/badge/Python-3.8_%7C_3.9_%7C_3.10_%7C_3.11-blue?logo=python&logoColor=white)
[![Stable Version](https://img.shields.io/pypi/v/sqlalchemy-bind-manager?color=blue)](https://pypi.org/project/sqlalchemy-bind-manager/)
[![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta)

[![Python tests](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-tests.yml)
[![Bandit checks](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-bandit.yml/badge.svg?branch=main)](https://github.com/febus982/sqlalchemy-bind-manager/actions/workflows/python-bandit.yml)
[![Maintainability](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/maintainability)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/0140f7f4e559ae806887/test_coverage)](https://codeclimate.com/github/febus982/sqlalchemy-bind-manager/test_coverage)

[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

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
