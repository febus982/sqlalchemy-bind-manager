## Alembic support in `SQLAlchemyBindManager`

[Alembic](https://alembic.sqlalchemy.org/en/latest/)
is a database migration tool widely used with SQLAlchemy.

While the installation and configuration of Alembic is not
in the scope of this package, `SQLAlchemyBindManager` class
provides the method `get_bind_mappers_metadata()` for an easier
integration with Alembic when using multiple binds. It will
return each bind metadata organised in a dictionary, using
the bind names as keys.

Alembic provides templates for synchronous engines and for
asynchronous engines, but there is no template supporting
both at the same time.

You can find an example Alembic configuration that works
with synchronous and asynchronous engines at the same time,
using the `SQLAlchemyBindManager` helper method, based on
the following directory structure:

```
├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions
└── alembic.ini
```

## alembic.ini

/// details | alembic.ini
```
--8<-- "docs/manager/alembic/alembic.ini"
```
///

## env.py

/// details | env.py
``` py
--8<-- "docs/manager/alembic/env.py"
```
///

## script.py.mako

/// details | script.py.mako
``` py
--8<-- "docs/manager/alembic/script.py.mako"
```
///
