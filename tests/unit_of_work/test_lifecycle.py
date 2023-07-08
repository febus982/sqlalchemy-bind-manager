import pytest

from sqlalchemy_bind_manager.exceptions import RepositoryNotFound


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
    with pytest.raises(RepositoryNotFound):
        uow.repository("Not existing")
