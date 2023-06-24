## Use the Unit Of Work to share a session among multiple repositories

It is possible we need to run several operations in a single database get_session. While a single
repository provide by itself an isolated session for single operations, we have to use a different
approach for multiple operations.

We can use the `UnitOfWork` or the `AsyncUnitOfWork` class to provide a shared session to
be used for repository operations, **assuming the same bind is used for all the repositories**.

/// admonition | The direct use of `SQLAlchemyRepository` and `SQLAlchemyAsyncRepository` classes is not yet supported
    type: warning
///

```python
class MyRepo(SQLAlchemyRepository):
    _model = MyModel
class MyOtherRepo(SQLAlchemyRepository):
    _model = MyOtherModel

bind = sa_manager.get_bind()
uow = UnitOfWork(bind, (MyRepo, MyOtherRepo))

with uow.transaction():
    uow.MyRepo.save(some_model)
    uow.MyOtherRepo.save(some_other_model)

# Optionally disable the commit/rollback handling
with uow.transaction(read_only=True):
    model1 = uow.MyRepo.get(1)
    model2 = uow.MyOtherRepo.get(2)
```

Both the UnitOfWork classes create an internal `scoped_session` or `async_scoped_session`, behaving
in the same way at the repositories do. This provides the freedom to tune the session lifecycle based
on our application requirements (e.g. one unit of work per http request, per domain, etc.)
