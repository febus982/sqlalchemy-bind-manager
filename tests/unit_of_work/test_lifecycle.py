async def test_repositories_are_initialised_with_uow_session(
    sa_bind, repository_class, model_classes, uow_class
):
    class RepoClass(repository_class):
        _model = model_classes[0]

    class ChildRepoClass(repository_class):
        _model = model_classes[1]

    repository_classes = [RepoClass, ChildRepoClass]
    uow = uow_class(
        bind=sa_bind,
        repositories=repository_classes,
    )
    for repo_class in repository_classes:
        assert hasattr(uow, repo_class.__name__)
        repo = getattr(uow, repo_class.__name__)
        assert not hasattr(repo, "_session_handler")
        assert hasattr(repo, "_external_session")
        assert getattr(repo, "_external_session") is uow._transaction_handler.session
