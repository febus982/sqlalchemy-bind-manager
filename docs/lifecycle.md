## When should you create each component?

### Bind manager

The `SQLAlchemyBindManager` object holds all the SQLAlchemy Engines, which
are supposed to be global objects. Therefore it should be created on application
startup and be globally accessible.

From SQLAlchemy documentation:

> The Engine is intended to normally be a permanent fixture established up-front
> and maintained throughout the lifespan of an application.

### Repositories

[SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it)
recommends we create `Session` object at the beginning of a logical operation where
database access is potentially anticipated.

The repository starts a `Session` for each _operation_, in order to maintain isolation.
This means you can create a repository object almost whenever you want.

/// details | There two exceptions: creating repositories in global variables or concurrent asyncio tasks
    type: warning
The repository creates and maintain the lifecycle of a session object to avoid
emitting unnecessary queries to refresh the model state on new session.

The session is not thread safe, therefore the repository is not thread safe as well.

Check the [Notes on multithreaded applications](/manager/session/#note-on-multithreaded-applications)

The `AsyncSession` [is not safe on concurrent asyncio tasks](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks),
therefore the same repository instance can't be used in multiple asyncio tasks like
when using `asyncio.gather()`
///

Even using multiple repository instances will work fine, however as they will have completely
different sessions, it's likely that the second repository will fire additional SELECT queries
to get the state of the object prior to saving it.

/// details | Example
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_bind_manager import SQLAlchemyBindManager ,SQLAlchemyConfig
from sqlalchemy_bind_manager.repository import SQLAlchemyRepository

config = SQLAlchemyConfig(
    engine_url="sqlite:///./sqlite.db",
    engine_options=dict(connect_args={"check_same_thread": False}, echo=True),
    session_options=dict(expire_on_commit=False),
)

sa_manager = SQLAlchemyBindManager(config={})

class MyModel(sa_manager.get_bind().model_declarative_base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

def update_my_model():
    # Create 2 instances of the same repository
    repo = SQLAlchemyRepository(sa_manager.get_bind(), model_class=MyModel)
    repo2 = SQLAlchemyRepository(sa_manager.get_bind(), model_class=MyModel)
    
    o = repo.get(1)
    o.name = "John"
    
    repo2.save(o)

update_my_model()
```
///

The recommendation is of course to use the same repository instance, where possible,
and structure your code in a way to match the single repository instance approach.

For example a strategy similar to this would be optimal, if possible:

* Create repositories
* Retrieve all the models you need
* Do the changes you need, as per business logic
* Save all the changed models as needed

/// tip | Using multiple repository instances is the only way to safely use concurrent asyncio tasks

///

### Unit of work

The Unit of Work session management follows the **same exact rules as the repository**,
therefore you should approach the creation af a `UnitOfWork` object in the same way.
