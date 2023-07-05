## When should you create each component?

### Bind manager

The `SQLAlchemyBindManager` object holds all the SQLAlchemy Engines, which
are supposed to be global objects, therefore it should be created on application
startup and be globally accessible.

From SQLAlchemy documentation:

> The Engine is intended to normally be a permanent fixture established up-front
> and maintained throughout the lifespan of an application.

### Repositories

[SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it)
recommends we create `Session` object at the beginning of a logical operation where
database access is potentially anticipated.

The repository keeps a `Session` object scoped to its lifecycle to avoid unnecessary queries,
and executes a transaction for each _operation_ to maintain isolation. This means you can create
a repository object almost whenever you want, as long as you don't run parallel operations.

The repository is safe in multithreaded applications and in concurrent asyncio tasks, this means
that potentially you can save it in a global variable, and it will have a different `Session`
in each thread or asyncio task.

Even if the repository can be used with concurrency or parallelism, remember SQLAlchemy models
belong to a single `Session`, so sharing the same models in multiple threads or asyncio tasks
will cause problems.

What you can do is:

* Save the repositories in global variables and start a thread / asyncio task to handle
  a scoped request (e.g. one thread per HTTP request)

What you cannot do is:

* Get a list of models
* Save the models using `save()` in parallel threads / tasks (each task will have a different session)

/// tip | The recommendation is of course to try to use a single repository instance, where possible.

For example a strategy similar to this would be optimal, if possible:

* Create repositories
* Retrieve all the models you need
* Do the changes you need, as per business logic, eventually using multiple threads / tasks
* Save all the changed models as needed

///

### Unit of work

The Unit of Work session management follows the **same exact rules as the repository**,
therefore you should approach the creation af a `UnitOfWork` object in the same way.
