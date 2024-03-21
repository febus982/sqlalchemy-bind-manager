from unittest.mock import MagicMock

import pytest

from sqlalchemy_bind_manager.exceptions import RepositoryNotFoundError


async def test_repositories_are_initialised_with_uow_session(
    sa_bind, repository_class, model_classes, uow_class
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    class ChildRepoClass(repository_class):
        _model = model_classes[1]

    repository_classes = [RepoClass, ChildRepoClass]
    uow = uow_class(bind=sa_bind)
    uow.register_repository(RepoClass.__name__, RepoClass)
    uow.register_repository("ChildRepoClass", repository_class, model_classes[1])

    for repo_class in repository_classes:
        repo = uow.repository(repo_class.__name__)
        assert repo is not None
        assert not hasattr(repo, "_session_handler")
        assert hasattr(repo, "_external_session")
        assert (
            getattr(repo, "_external_session") is uow._session_handler.scoped_session()
        )


async def test_raises_exception_if_repository_not_found(sa_bind, uow_class):
    uow = uow_class(bind=sa_bind)
    with pytest.raises(RepositoryNotFoundError):
        uow.repository("Not existing")


@pytest.mark.parametrize(
    ["submitted_args", "submitted_kwargs", "received_args", "received_kwargs"],
    [
        pytest.param(
            ("1", "2"),
            dict(a="b"),
            ("2",),
            dict(model_class="1", a="b"),
            id="first_arg_model_class_if_no_kwarg",
        ),
        pytest.param(
            tuple([]),
            dict(a="b", model_class="c"),
            tuple([]),
            dict(model_class="c", a="b"),
            id="model_class_rearranged_if_in_kwargs",
        ),
        pytest.param(
            tuple([]),
            dict(a="b"),
            tuple([]),
            dict(model_class=None, a="b"),
            id="model_class_default_to_none",
        ),
        pytest.param(
            tuple([]),
            dict(a="b", session="c"),
            tuple([]),
            dict(model_class=None, a="b"),
            id="session_removed_from_kwargs",
        ),
    ],
)
async def test_additional_arguments_are_forwarded(
    sa_bind,
    uow_class,
    submitted_args: tuple,
    submitted_kwargs: dict,
    received_args: tuple,
    received_kwargs: dict,
):
    repo = MagicMock()

    uow = uow_class(bind=sa_bind)
    uow.register_repository("r", repo, *submitted_args, **submitted_kwargs)

    repo.assert_called_once_with(
        *received_args, session=uow._session_handler.scoped_session(), **received_kwargs
    )
