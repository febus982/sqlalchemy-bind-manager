import logging
import os
from asyncio import get_event_loop

from alembic import context
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncEngine

from sqlalchemy_bind_manager import SQLAlchemyAsyncConfig, SQLAlchemyBindManager

################################################################
## Note: The bind_config, sa_manager and models are normally  ##
## implemented in an application. This is only an example!    ##
################################################################
bind_config = {
    "default": SQLAlchemyAsyncConfig(
        engine_url=f"sqlite+aiosqlite:///{os.path.dirname(os.path.abspath(__file__))}/sqlite.db",
        engine_options=dict(
            connect_args={
                "check_same_thread": False,
            },
            echo=False,
            future=True,
        ),
    ),
}

sa_manager = SQLAlchemyBindManager(config=bind_config)

class BookModel(sa_manager.get_bind().declarative_base):
    id = Column(Integer)
    title = Column(String)
################################################################
## Note: The bind_config, sa_manager and models are normally  ##
## implemented in an application. This is only an example!    ##
################################################################


USE_TWOPHASE = False

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

logger = logging.getLogger("alembic.env")
target_metadata = sa_manager.get_bind_mappers_metadata()
db_names = target_metadata.keys()
config.set_main_option("databases", ",".join(db_names))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # for the --sql use case, run migrations for each URL into
    # individual files.

    engines = {}
    for name in db_names:
        engines[name] = {}
        engines[name]["url"] = sa_manager.get_bind(name).engine.url

    for name, rec in engines.items():
        logger.info(f"Migrating database {name}")
        file_ = f"{name}.sql"
        logger.info(f"Writing output to {file_}")
        with open(file_, "w") as buffer:
            context.configure(
                url=rec["url"],
                output_buffer=buffer,
                target_metadata=target_metadata.get(name),
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
            )
            with context.begin_transaction():
                context.run_migrations(engine_name=name)


def do_run_migration(conn, name):
    context.configure(
        connection=conn,
        upgrade_token=f"{name}_upgrades",
        downgrade_token=f"{name}_downgrades",
        target_metadata=target_metadata.get(name),
    )
    context.run_migrations(engine_name=name)


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    # for the direct-to-DB use case, start a transaction on all
    # engines, then run all migrations, then commit all transactions.

    engines = {}
    for name in db_names:
        engines[name] = {}
        engines[name]["engine"] = sa_manager.get_bind(name).engine

    for name, rec in engines.items():
        engine = rec["engine"]
        if isinstance(engine, AsyncEngine):
            rec["connection"] = conn = await engine.connect()

            if USE_TWOPHASE:
                rec["transaction"] = await conn.begin_twophase()
            else:
                rec["transaction"] = await conn.begin()
        else:
            rec["connection"] = conn = engine.connect()

            if USE_TWOPHASE:
                rec["transaction"] = conn.begin_twophase()
            else:
                rec["transaction"] = conn.begin()

    try:
        for name, rec in engines.items():
            logger.info(f"Migrating database {name}")
            if isinstance(rec["engine"], AsyncEngine):

                def migration_callable(*args, **kwargs):
                    return do_run_migration(*args, name=name, **kwargs)

                await rec["connection"].run_sync(migration_callable)
            else:
                do_run_migration(name, rec)

        if USE_TWOPHASE:
            for rec in engines.values():
                if isinstance(rec["engine"], AsyncEngine):
                    await rec["transaction"].prepare()
                else:
                    rec["transaction"].prepare()

        for rec in engines.values():
            if isinstance(rec["engine"], AsyncEngine):
                await rec["transaction"].commit()
            else:
                rec["transaction"].commit()
    except:
        for rec in engines.values():
            if isinstance(rec["engine"], AsyncEngine):
                await rec["transaction"].rollback()
            else:
                rec["transaction"].rollback()
        raise
    finally:
        for rec in engines.values():
            if isinstance(rec["engine"], AsyncEngine):
                await rec["connection"].close()
            else:
                rec["connection"].close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    loop = get_event_loop()
    if loop.is_running():
        loop.create_task(run_migrations_online())
    else:
        loop.run_until_complete(run_migrations_online())
