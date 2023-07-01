Using the session is the same as standard SQLAlchemy. The recommended approach
is using the `get_session()` context manager, so you don't need to manage the
session life cycle.

```python
# Persist an object
o = ImperativeModel()
o.name = "John"
with sa_manager.get_session() as session:
    session.add(o)
    session.commit()

# We can also get the `session_class` property of the bind,
# but t
with sa_manager.get_bind().session_class()() as session:
    session.add(o)
    session.commit()
```

## Note on multithreaded applications

Global variables are shared between different threads in python. If your application uses
multiple threads, like spawning a thread per request, then you should not store an
initialised session in a global variable, otherwise the state of your models will be shared
among the threads and produce undesired changes in the database.

This is not thread safe:

/// note | db.py (a module to have an easy to use session)
```python
session = sa_manager.get_session()
```
///


/// note | some_other_module.py (a module to have an easy-to=use session)
```python
from db import session

session.add(model)
session.commit()
```
///


This instead would be thread safe:

/// note | some_other_module.py (a module to have an easy-to=use session)

```python
def do_something():
    session = sa_manager.get_session()
    session.add(model)
    session.commit()
    session.close()

do_something()
```

The `do_something` function can be also in another method, as long as
the `session` variable has no global scope it will be safe.
///

/// tip | Using the `get_session()` context manager is much easier

///

If you truly need to have a long-lived session in a variable with global scope,
you'll need to use a scoped session like this:

```python
from sqlalchemy.orm import scoped_session

session = scoped_session(sa_manager.get_bind().session_class())
```

Handling the life cycle of scoped sessions is not supported by this documentations.
Please refer to [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/contextual.html)
about this.
