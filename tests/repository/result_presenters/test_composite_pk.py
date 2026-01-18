from unittest.mock import Mock, patch

import pytest

from sqlalchemy_bind_manager._repository.common import get_model_pk_name


def test_exception_raised_if_multiple_primary_keys():
    with (
        patch(
            "sqlalchemy_bind_manager._repository.common.inspect",
            return_value=Mock(primary_key=["1", "2"]),
        ),
        pytest.raises(NotImplementedError),
    ):
        get_model_pk_name(str)
