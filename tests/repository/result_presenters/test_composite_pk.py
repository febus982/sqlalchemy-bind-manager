from unittest.mock import Mock, patch

import pytest

from sqlalchemy_bind_manager._repository.result_presenters import _pk_from_result_object


def test_exception_raised_if_multiple_primary_keys():
    with patch(
        "sqlalchemy_bind_manager._repository.result_presenters.inspect",
        return_value=Mock(primary_key=["1", "2"]),
    ), pytest.raises(NotImplementedError):
        _pk_from_result_object("irrelevant")
