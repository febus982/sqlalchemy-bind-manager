# V1 redesign: transaction lifecycle

This document describes the planned redesign of session and transaction management
for the V1 release.

The short version: **the repository stops deciding when to commit.** A new
`TransactionScope` owns the transaction boundary, repositories resolve their session
from it per call, and the boundary can be attached to whatever lifecycle your
application already has — a FastAPI dependency, a CLI command, a worker handler, or a
plain `with` block.

## Why change

Today there are three ways to manage a transaction, and which one you get is decided by
a constructor argument:

```python
SQLAlchemyRepository(bind=...)      # a session per operation, repository commits
UnitOfWork(bind).transaction()      # a session per block, unit of work commits
SQLAlchemyRepository(session=...)   # undocumented; the caller owns everything
```

That choice silently changes the contract of the methods you call.

### `save()` means two different things

With a bind, `save()` returns a model with its primary key populated. With an external
session it does not, because the repository calls `session.add()` without flushing:

```python
with uow.transaction():
    model = repo.save(my_model)
    model.model_id            # None

model.model_id                # 2 - only after the block committed
```

Same method, same signature, same `-> MODEL` return type. Code cannot be written to work
in both modes. It also means an `IntegrityError` surfaces at the end of the transaction
rather than at the call that caused it.

### Operations cannot be composed

Two `save()` calls against a bind-constructed repository are two transactions. If the
second fails, the first stays committed. There is no way to opt into atomicity without
switching to a different class entirely.

### Some read methods commit

The repository already has the mechanism to avoid this. `_get_session(commit=False)`
resolves to `SessionHandler.get_session(read_only=True)`, which skips the commit, and
`get()` and `get_many()` use it correctly.

The three `find` variants simply never pass the flag, so they take the default
`commit=True` path and commit a read:

```text
save():                  BEGIN, FLUSH, COMMIT
get():                   BEGIN                <- commit=False, correct
get_many():              BEGIN                <- commit=False, correct
find():                  BEGIN, COMMIT        <- flag not passed
paginated_find():        BEGIN, COMMIT        <- flag not passed
cursor_paginated_find(): BEGIN, COMMIT        <- flag not passed
```

This is a self-contained bug: passing `commit=False` at those three call sites in each of
the sync and async repositories fixes it today, independently of the rest of this
redesign. Under the new model it cannot recur, because the repository has no commit path
at all.

### A unit of work registered once and used per request is broken

`register_repository()` captures a session at registration time, while `transaction()`
resolves one again at call time. Register at startup and use from a request, and they are
different sessions:

```text
repo session is the transaction session: False
InvalidRequestError: Autobegin is disabled on this Session
```

This fails for `UnitOfWork` across threads and `AsyncUnitOfWork` across asyncio tasks —
which is the natural way to wire either into a web framework.

### The async session registry grows without bound

`AsyncSessionHandler` scopes sessions on `asyncio.current_task` and never calls
`remove()`, so both the `AsyncSession` and the `Task` handle are retained forever:

```text
after  50 requests: registry holds  50 sessions
after 100 requests: registry holds 100 sessions
after 150 requests: registry holds 150 sessions
```

/// warning | The current documentation makes this worse

`Components life cycle` advises storing repositories in global variables, which is
exactly the usage that triggers the retention.
///

## The new model

Three components, each with one responsibility.

```text
SQLAlchemyBindManager     engines, pools, config          application lifetime
        |  transaction_scope(bind_name) ->
        v
TransactionScope          transaction boundary,           application lifetime
                          current session                 (one per logical scope)
        |  constructor argument ->
        v
SQLAlchemyRepository      queries, model mapping          application lifetime
                          no session state                (singleton, injectable)
```

### Bind manager

Unchanged in role — engines, pools, configuration, declarative bases, `dispose_engines()`.
It gains two factory methods:

```python
scope = sa_manager.transaction_scope()                    # sync bind
scope = sa_manager.async_transaction_scope("analytics")   # async bind
```

Two methods rather than one returning a union, so the static type is known at the call
site. Each raises `UnsupportedBindError` if the bind type does not match.

/// warning | Every call returns a new, independent scope

The manager does not cache scopes. Create them once at startup and hold the references.
Calling the factory inside a request handler produces a scope with no active transaction.
///

### Transaction scope

```python
class TransactionScope:
    @contextmanager
    def transaction(self) -> Iterator[Session]: ...
    @contextmanager
    def savepoint(self) -> Iterator[Session]: ...

    def current_session(self) -> Session: ...
```

`transaction()` yields the `Session` as a deliberate escape hatch for raw SQL and bulk
operations. It participates in the same transaction, so it composes rather than bypasses.

The current session is stored in a `ContextVar`, which isolates correctly across both
asyncio tasks and threads without any framework support.

### Repository

The repository holds a scope, never a session, and follows one rule everywhere:

- **never** commit, begin, or close
- **always** flush on write, so the postcondition is identical in every context and
  integrity errors raise at the call site
- reads neither commit nor flush beyond SQLAlchemy's autoflush

```python
def save(self, instance: MODEL) -> MODEL:
    self._fail_if_invalid_models([instance])
    session = self._scope.current_session()
    session.add(instance)
    session.flush()
    return instance
```

`SQLAlchemyRepositoryInterface` and `SQLAlchemyAsyncRepositoryInterface` are unchanged.
They are what your dependency injection binds to, and this redesign does not touch them.

## Transaction semantics

### Commit only when something was written

```python
with scope.transaction():
    repo.save(user)
```

- clean exit **with** writes → `COMMIT`
- clean exit **without** writes → `ROLLBACK`
- exception → `ROLLBACK`, exception propagates

Because SQLAlchemy cannot read without a transaction, read-only code paths still open
one. Committing them is pointless, so the boundary detects whether any write actually
happened and rolls back when none did.

/// details | How writes are detected
    type: tip

The obvious check does not work. Because repositories always flush,
`session.new / dirty / deleted` are empty at exit for a flushed write *and* for a pure
read — indistinguishable.

Detection therefore combines two signals:

| case | events | pending state at exit |
|---|---|---|
| read only | `False` | empty |
| `save()` + flush | `True` | empty |
| raw `session.execute(insert(...))` | `True` | empty |
| `session.add()` with no flush | `False` | `new=1` |

```python
should_commit = (
    wrote_via_events                                      # after_flush / do_orm_execute
    or session.new or session.dirty or session.deleted    # unflushed escape-hatch writes
)
```
///

### Nesting is refused

Calling `transaction()` inside an active transaction on the same scope raises
`TransactionAlreadyActiveError`. A block that silently joins claims ownership it does not
have, and presumes a transaction context the surrounding code never established.

Three rules follow:

- **Boundaries belong to entry points** — middleware, CLI commands, worker handlers — not
  to services. A service that opens its own boundary cannot be called from anywhere that
  already has one.
- **An independent transaction means a second scope.** Two scopes over the same bind hold
  separate sessions and separate transactions, which is how you run a subsystem in its own
  transaction while the request transaction is open.
- **Partial rollback means `savepoint()`.**

```python
with scope.transaction():
    repo.save(a)

    with scope.savepoint():
        repo.save(risky)      # can fail without killing the request
```

/// details | Why savepoints are not optional sugar
    type: tip

A savepoint is a marker inside an open transaction. You can undo back to it without
destroying the whole transaction:

```sql
BEGIN;
  INSERT INTO users ...;         -- (1)
  SAVEPOINT sp1;
    INSERT INTO audit_log ...;   -- (2)
  ROLLBACK TO SAVEPOINT sp1;     -- undoes (2), keeps (1)
COMMIT;
```

Once a `flush()` fails, SQLAlchemy marks the transaction inactive and refuses further
work until something rolls back. So "try this, recover if it fails" genuinely requires a
savepoint — there is no other way to express it.
///

### Concurrency

Threads and asyncio tasks behave differently, and the difference matters:

| | sync scope | async scope |
|---|---|---|
| context inheritance | none — each thread starts with a fresh context | child tasks inherit |
| concurrency guard | not needed | required |

Inheritance in asyncio is load-bearing: it is what allows a transaction opened in
Starlette middleware to reach a handler running in a child task. But SQLAlchemy does not
detect concurrent use of a single `AsyncSession`, so the async scope raises
`ConcurrentSessionError` when a second task begins an operation while another is in
flight:

```python
async with scope.transaction():
    await asyncio.gather(repo.get(1), repo.get(2))   # ConcurrentSessionError
```

Sequential use from a child task is fine, and a repository method calling another is
re-entrant.

The sync scope needs no guard. A `ThreadPoolExecutor` worker calling a repository raises
`NoActiveTransactionError`, because its context is empty — a loud failure rather than a
silently wrong session.

## New exceptions

| Exception | Raised when |
|---|---|
| `NoActiveTransactionError` | a repository method or `savepoint()` is called outside `transaction()` |
| `TransactionAlreadyActiveError` | `transaction()` is nested on the same scope |
| `ConcurrentSessionError` | two tasks operate on one session simultaneously |

## Using it

Nothing in the design is framework-specific — the scope is a context manager.

### With dependency injection

The application layer depends only on the repository protocols and never sees the
transaction machinery:

```python
# composition root, at startup
sa_manager = SQLAlchemyBindManager(config)
main = sa_manager.async_transaction_scope()

container.bind(UserRepositoryProtocol, UserRepository(main))

# application layer - knows nothing about scopes or sessions
async def create_user(users: UserRepositoryProtocol) -> None:
    await users.save(User(name="Federico"))
```

### FastAPI

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sa_manager.dispose_engines()

async def transaction():
    async with main.transaction():
        yield

app = FastAPI(lifespan=lifespan, dependencies=[Depends(transaction)])
```

`lifespan=` is the application lifecycle. `dependencies=[...]` is the **request**
lifecycle, despite living on the constructor.

/// admonition | Do not use `@app.middleware("http")` for the transaction boundary
    type: warning

Starlette's exception handling runs *inside* `call_next`, so a handler exception has
already been converted into a 500 response before the middleware sees it. The block exits
cleanly and commits a failed request.

A `yield` dependency has the exception thrown into it, so rollback works correctly.
///

/// warning | Background tasks run after the response

The request transaction is already closed by then, so a repository call raises
`NoActiveTransactionError`. Background tasks must open their own `scope.transaction()`.

Global dependencies also do not cover exception handlers or middleware, which run outside
the dependency stack.
///

### Synchronous applications

No asyncio required anywhere:

```python
scope = sa_manager.transaction_scope()
repo = UserRepository(scope)

with scope.transaction():
    repo.save(User(name="Federico"))
```

Threads are isolated automatically — each thread starts with a fresh context, so every
thread must open its own transaction.

## Extending the repository

Subclassing the repository to add custom methods is a supported use case, but until now
the API those methods need was never documented — the examples show a custom method with
an empty body, and `_get_session()` is not mentioned anywhere. V1 defines that contract.

Custom methods use `self._session`, plus the query helpers that build the statements the
built-in methods already use:

```python
class ModelRepository(SQLAlchemyRepository[MyModel]):
    _model = MyModel

    def find_active(self) -> List[MyModel]:
        stmt = self._find_query({"status": "active"})
        return [x for x in self._session.execute(stmt).scalars()]

    def archive(self, instance: MyModel) -> None:
        self._fail_if_invalid_models([instance])
        instance.status = "archived"
        self._session.flush()
```

The supported members for subclasses:

| Member | Purpose |
|---|---|
| `self._session` | the session for the active transaction |
| `self._model` | the mapped class |
| `self._max_query_limit` | pagination ceiling, overridable |
| `self._find_query(search_params, order_by)` | build a filtered `Select` |
| `self._paginate_query_by_page(stmt, page, items_per_page)` | offset pagination |
| `self._cursor_paginated_query(...)` | cursor pagination |
| `self._count_query(stmt)` | wrap a query in a count |
| `self._model_pk()` | primary key column name |
| `self._fail_if_invalid_models(objects)` | reject models from another repository |

Everything else is internal and may change without notice.

### Migrating existing subclasses

| Today | Under V1 | What you see |
|---|---|---|
| `with self._get_session() as s: s.add(x)` | commit moves to the boundary | works unchanged |
| `with self._get_session(commit=False) as s:` | behaviour unchanged | works unchanged |
| custom method called outside a transaction | `NoActiveTransactionError` | loud failure |
| `self._external_session` / `self._session_handler` | removed | `AttributeError` |

`_get_session()` keeps working through the V1 deprecation window — it yields the current
session and emits a `DeprecationWarning`, so existing subclasses run unmodified while you
migrate them to `self._session`.

/// details | Will my custom write methods silently stop committing?
    type: tip

No. This is the natural worry, since `_get_session()` used to commit when the block
exited and the repository no longer commits at all.

A custom method that leaves a pending `add()` still gets committed, because the
transaction boundary inspects `session.new / dirty / deleted` before deciding. The write
is picked up there instead. Only the **timing** changes: the commit happens when the
surrounding `transaction()` block exits rather than when your method returns.

What does change loudly is calling such a method with no transaction open — that raises
`NoActiveTransactionError` instead of quietly committing on its own.
///

## Migration

Nothing is removed in the V1 release. The legacy entry points keep working and emit
`DeprecationWarning`.

| Today | V1 | Next major |
|---|---|---|
| `Repository(bind=...)` | warns; autocommit per operation preserved | removed |
| `Repository(session=...)` | warns; session wrapped in an adapter scope | removed |
| `UnitOfWork` / `AsyncUnitOfWork` | warns; thin shim over `TransactionScope` | removed |
| `register_repository()` / `repository(name)` | warns | removed |
| `SessionHandler` / `AsyncSessionHandler` | private already — removed | — |
| `RepositoryNotFoundError` | kept while `register_repository` lives | removed |

The repository keeps its single rule — never commit, always flush. Legacy autocommit is
reproduced by an adapter: when constructed from a bind, each call is wrapped in an
implicit transaction, so the commit still happens at a boundary.

Reimplementing `UnitOfWork` as a shim over `TransactionScope` fixes the cross-task bug and
the registry leak on the deprecated path too, so users who have not migrated still get
the fixes.

/// warning | One deliberate behaviour change on the legacy path

`find()`, `paginated_find()` and `cursor_paginated_find()` stop committing. This is a
bugfix, but it is a behaviour change if you were relying on a read to flush pending work.
///

## Design decisions

/// details | Why not keep `scoped_session` as the registry?
    type: tip

`scoped_session` and `async_scoped_session` are registries, not what makes async work —
that is `create_async_engine`, `async_sessionmaker` and `AsyncSession`, none of which
change.

The decisive reason is the middleware pattern. Starlette's `BaseHTTPMiddleware` runs the
downstream application in a child task, so a registry keyed on `asyncio.current_task`
hands the handler a *different* session from the one the middleware opened, with no
transaction and no error:

```text
middleware opens txn, handler runs in a child task
  ContextVar           -> handler sees middleware session: True
  async_scoped_session -> handler sees middleware session: False
```

Fixing that means supplying a `ContextVar`-backed `scopefunc`, at which point the registry
is a `ContextVar` plus a proxy plus a `remove()` obligation, for the same result.

`ContextVar` also unifies the sync and async scoping models. `scoped_session` needs a
different scopefunc for each (thread-local versus `current_task`), which is why
`SessionHandler` and `AsyncSessionHandler` exist as separate classes today.
///

/// details | Why is there no read-only transaction?
    type: tip

An earlier draft included `read_transaction()`. Once the boundary commits only when
something was written, a read-only variant is redundant as an optimisation — and as a
guarantee it is advisory only, since it is enforced in Python.

If you need a genuine read-only guarantee, configure a **second bind** pointing at a
read-only role or a replica. The database enforces it properly, and multiple binds are
already supported.
///

/// details | Why must repositories always flush?
    type: tip

It makes the postcondition of `save()` identical in every context: the primary key and
server-side defaults are populated when the call returns, whatever provided the session.

It also fixes error locality. Without a flush, an `IntegrityError` surfaces wherever the
transaction happens to commit — often in framework code far from the cause. With a flush,
it raises at the offending line.

The cost is a round trip per write, and SQL ordering within a transaction becomes visible
to the caller. That is the correct trade for a repository.
///

## Limitations

Cross-bind atomicity remains unsupported. Two-phase commit is not implemented, so a
transaction scope covers exactly one bind — the same limitation as today, now stated in
one place rather than implied.
