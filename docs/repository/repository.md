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
```

The classes provide some common use methods:

* `get`: Retrieve a model by identifier
* `save`: Persist a model
* `save_many`: Persist multiple models in a single transaction
* `delete`: Delete a model
* `find`: Search for a list of models (basically an adapter for SELECT queries)
* `paginated_find`: Search for a list of models, with pagination support
* `cursor_paginated_find`: Search for a list of models, with cursor based pagination support

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
garbage collector clean it up)

In this way we ensure the `Session` we use is isolated, and the same for all the operations we do with the
same Repository. 

This approach has a consequence: We can't use SQLAlchemy lazy loading, so we'll need to make sure relationship are always loaded eagerly,
using either approach:
* Setup your model/table relationships to always use always eager loading
* Implement ad-hoc methods to deal with relationships as necessary

Note that `AsyncSession` has [the same limitation on lazy loading](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads),
even when keeping the session opened, so it makes sense that the two Repository implementations behave consistently.
