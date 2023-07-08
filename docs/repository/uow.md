## Use the Unit Of Work to share a session among multiple repositories

It is possible we need to run several operations in a single database get_session. While a single
repository provide by itself an isolated session for single operations, we have to use a different
approach for multiple operations.

We can use the `UnitOfWork` or the `AsyncUnitOfWork` class to provide a shared session to
be used for repository operations.

```python
class MyRepo(SQLAlchemyRepository):
    _model = MyModel

bind = sa_manager.get_bind()
uow = UnitOfWork(bind)
uow.register_repository("repo_a", MyRepo)
# args and kwargs are forwarded so we can also use directly `SQLAlchemyRepository` class
uow.register_repository("repo_b", SQLAlchemyRepository, MyOtherModel)

with uow.transaction():
    uow.repository("repo_a").save(some_model)
    uow.repository("repo_b").save(some_other_model)

# Optionally disable the commit/rollback handling
with uow.transaction(read_only=True):
    model1 = uow.repository("repo_a").get(1)
    model2 = uow.repository("repo_b").get(2)
```

/// admonition | The unit of work implementation is still experimental.
    type: warning

There are some limitations in the current implementation that could radically change
the implementation:

* Distributed transactions are not yet supported. 
* The direct use of `SQLAlchemyRepository` and `SQLAlchemyAsyncRepository` classes is not yet supported.
///

Both the UnitOfWork classes create an internal `scoped_session` or `async_scoped_session`, behaving
in the same way at the repositories do. This provides the freedom to tune the session lifecycle based
on our application requirements (e.g. one unit of work per http request, per domain, etc.)
