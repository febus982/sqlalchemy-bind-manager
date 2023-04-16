def test_find_limit(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = [m for m in repo.find(limit=2)]
    assert len(results) == 2
    assert results[0].name == "Someone"
    assert results[1].name == "SomeoneElse"


def test_find_max_limit(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    repo._max_query_limit = 2
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = [m for m in repo.find(limit=2)]
    assert len(results) == 2
    assert results[0].name == "Someone"
    assert results[1].name == "SomeoneElse"


def test_find_offset(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    model = model_class(
        name="Someone",
    )
    repo.save(model)
    model2 = model_class(
        name="SomeoneElse",
    )
    repo.save(model2)
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo.save(model3)

    results = [m for m in repo.find(limit=2, offset=1)]
    assert len(results) == 2
    assert results[0].name == "SomeoneElse"
    assert results[1].name == "StillSomeoneElse"
