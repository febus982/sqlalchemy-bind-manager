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
