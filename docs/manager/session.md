Using the session is the same as standard SQLAlchemy, we just retrieve the session class
using the `get_session()` method.

```python
# Persist an object
o = ImperativeModel()
o.name = "John"
with sa_manager.get_bind().session_class()() as session:
    session.add(o)
    session.commit()

# or using the get_session() helper method for better readability
with sa_manager.get_session() as session:
    session.add(o)
    session.commit()
```

## Note on multithreaded applications

Global variables are shared between different threads in python. If your application uses
multiple threads, like spawning a thread per request, then you should not store an
initialised session in a global variable, otherwise the state of your models will be shared
among the threads and produce undesired changes in the database.

This is not thread safe:

```python
session = sa_manager.get_session()
session.add(model)
session.commit()
```

If you truly need to have a long-lived session you'll need to use a scoped session,
something like this:

```python
from sqlalchemy.orm import scoped_session

session = scoped_session(sa_manager.get_bind().session_class())
```

Handling the life cycle of scoped sessions is not supported by this documentations.
Please refer to [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/contextual.html)
about this.
