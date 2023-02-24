from sqlalchemy_bind_manager._unit_of_work import AsyncUnitOfWork


async def test_repositories_are_initialised_with_uow_session(
    sa_manager, repository_classes
):
    uow = AsyncUnitOfWork(
        bind=sa_manager.get_bind(),
        repositories=repository_classes,
    )
    for repo_class in repository_classes:
        assert hasattr(uow, repo_class.__name__)
        repo = getattr(uow, repo_class.__name__)
        assert not hasattr(repo, "_session_handler")
        assert hasattr(repo, "_external_session")
        assert getattr(repo, "_external_session") is uow._transaction_handler.session
