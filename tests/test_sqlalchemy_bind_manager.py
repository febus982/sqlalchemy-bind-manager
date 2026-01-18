from unittest.mock import patch

import pytest
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, registry

from sqlalchemy_bind_manager import (
    SQLAlchemyBindManager,
    SQLAlchemyConfig,
)
from sqlalchemy_bind_manager.exceptions import (
    InvalidConfigError,
    NotInitializedBindError,
)


@pytest.mark.parametrize(
    "supplied_config",
    [
        {"bind_name": "Invalid Config"},
        {
            "valid": SQLAlchemyConfig(
                engine_url="sqlite://",
                engine_options=dict(connect_args={"check_same_thread": False}),
                session_options=dict(expire_on_commit=False),
            ),
            "invalid": "Invalid Config",
        },
        "Invalid single config",
    ],
)
def test_invalid_config_raises_exception(supplied_config):
    # We consciously ignore the type to supply an invalid config
    with pytest.raises(InvalidConfigError):
        SQLAlchemyBindManager(supplied_config)  # type: ignore


def test_initialised_bind_raises_error(single_config):
    sa_manager = SQLAlchemyBindManager(single_config)
    with pytest.raises(NotInitializedBindError):
        sa_manager.get_session("uninitialised bind")


def test_single_config_creates_default_bind(single_config):
    sa_manager = SQLAlchemyBindManager(single_config)

    assert len(sa_manager.get_binds()) == 1

    default_bind = sa_manager.get_bind()
    assert default_bind is not None
    assert isinstance(sa_manager.get_mapper(), registry)
    assert isinstance(sa_manager.get_session(), Session)
    assert sa_manager.get_session().get_bind() == default_bind.engine


def test_multiple_binds(multiple_config):
    sa_manager = SQLAlchemyBindManager(multiple_config)
    assert len(sa_manager.get_binds()) == 2

    mappers_metadata = sa_manager.get_bind_mappers_metadata()
    assert len(mappers_metadata) == 2
    for key in ["default", "async"]:
        assert key in mappers_metadata
        assert isinstance(mappers_metadata[key], MetaData)

    default_bind = sa_manager.get_bind()
    assert default_bind is not None
    assert isinstance(sa_manager.get_mapper(), registry)
    assert isinstance(sa_manager.get_session(), Session)

    async_bind = sa_manager.get_bind("async")
    assert async_bind is not None
    assert isinstance(sa_manager.get_mapper("async"), registry)
    assert isinstance(sa_manager.get_session("async"), AsyncSession)


def test_engine_is_disposed_on_cleanup(multiple_config):
    """Test that engines are disposed synchronously during garbage collection.

    This test verifies that both sync and async engines are properly disposed
    using synchronous disposal (sync_engine.dispose() for async engines).
    """
    sa_manager = SQLAlchemyBindManager(multiple_config)
    sync_engine = sa_manager.get_bind("default").engine
    async_engine = sa_manager.get_bind("async").engine

    original_sync_dispose = sync_engine.dispose
    # For async engines, we now use sync_engine.dispose() for safe cleanup
    original_async_sync_dispose = async_engine.sync_engine.dispose

    with (
        patch.object(
            sync_engine,
            "dispose",
            wraps=original_sync_dispose,
        ) as mocked_dispose,
        patch.object(
            async_engine.sync_engine,
            "dispose",
            wraps=original_async_sync_dispose,
        ) as mocked_async_sync_dispose,
    ):
        sa_manager = None

    mocked_dispose.assert_called_once()
    mocked_async_sync_dispose.assert_called_once()


def test_atexit_cleanup_disposes_all_managers(multiple_config):
    """Test that the atexit handler disposes all tracked manager instances."""
    from sqlalchemy_bind_manager._bind_manager import _cleanup_all_managers

    sa_manager = SQLAlchemyBindManager(multiple_config)

    with patch.object(
        sa_manager,
        "_dispose_sync",
    ) as mocked_dispose_sync:
        _cleanup_all_managers()

    mocked_dispose_sync.assert_called_once()
