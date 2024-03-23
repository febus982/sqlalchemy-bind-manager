## Repository / Unit of work

The `SQLAlchemyRepository` and `SQLAlchemyAsyncRepository` class can be used directly or by extending them.

```python
from sqlalchemy_bind_manager.repository import SQLAlchemyRepository


class MyModel(declarative_base):
    pass

# Direct usage
repo_instance = SQLAlchemyRepository(
    sa_manager.get_bind(),
    model_class=MyModel
)

# Child class usage (when you need to implement custom repository methods)
class ModelRepository(SQLAlchemyRepository[MyModel]):
    _model = MyModel
    
    def _some_custom_method_implemented(self):
        ...

repo_instance_2 = ModelRepository(sa_manager.get_bind())
```

The classes provide some common use methods:

* `get`: Retrieve a model by identifier
* `save`: Persist a model
* `save_many`: Persist multiple models in a single transaction
* `delete`: Delete a model
* `find`: Search for a list of models (basically an adapter for SELECT queries)
* `paginated_find`: Search for a list of models, with pagination support
* `cursor_paginated_find`: Search for a list of models, with cursor based pagination support

/// details | Typing and Interfaces
    type: tip

The repository classes are fully typed (as the rest of this package). The repositories
implement interface classes that are available to allow better code decoupling
and inversion of control patterns such as
[dependency injection](https://en.wikipedia.org/wiki/Dependency_injection).

```python
from sqlalchemy_bind_manager.repository import SQLAlchemyRepositoryInterface, SQLAlchemyAsyncRepositoryInterface


def some_function(repository: SQLAlchemyRepositoryInterface[MyModel]):
    model = repository.get(123)
    ...


async def some_async_function(repository: SQLAlchemyAsyncRepositoryInterface[MyModel]):
    model = await repository.get(123)
    ...
```

Both repository and related interface are Generic, accepting the model class as a typing argument.
///

### Maximum query limit

Repositories have a maximum limit for paginated queries defaulting to 50 to
avoid pulling pages with too many items by mistake. You can override this limit
by overriding the `_max_query_limit` repository property. E.g.:

```python
class ModelRepository(SQLAlchemyRepository[MyModel]):
    _model = MyModel
    _max_query_limit: int = 2000
```

The query limit does not apply to the non paginated `find()`

## Session lifecycle in repositories

[SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it)
recommends we create `Session` object at the beginning of a logical operation where
database access is potentially anticipated.

Doing this too soon might cause unexpected effects, like unexpected updates being committed,
if the initialised session is shared among different repositories.

A `Repository` represents a generic interface to persist data object to a storage, not necessarily
using SQLAlchemy. It makes sense that the lifecycle of a `Session` follows the one of the Repository
(The assumption is: if we create a Repository, we're going to do a DB operation,
otherwise we wouldn't need one).

Each Repository instance create an internal scoped session. The session gets
automatically closed when the Repository instance is not referenced by any variable (and the
garbage collector cleans it up)

In this way we ensure the `Session` we use is isolated, and the same for all the operations we do with the
same Repository. 

This approach has a consequence: We can't use SQLAlchemy lazy loading, so we'll need to make sure relationship are always loaded eagerly,
using either approach:
* Setup your model/table relationships to always use always eager loading
* Implement ad-hoc methods to deal with relationships as necessary

Note that `AsyncSession` has [the same limitation on lazy loading](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads),
even when keeping the session opened, so it makes sense that the two Repository implementations behave consistently.

/// details | Lazy loading using `AsyncAttrs`

SQLAlchemy has recently added the `AsyncAttrs` model class mixin to allow lazy loading model attributes 
with `AsyncSession`, however having to `await` a model property introduce a coupling between the
application logic and the storage layer.

This would mean the application logic has to know about the storage layer and make a distinction
between sync and async models. This doesn't feel right, at least for now,
therefore it's not enabled by default.

If you want to attempt lazy loading refer to [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm)
///    
