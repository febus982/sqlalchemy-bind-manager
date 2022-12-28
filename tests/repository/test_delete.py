import pytest


def test_can_delete_by_pk(repository_class, model_class, sa_manager):
    model = model_class(
        model_id=1,
        name="Someone",
    )
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo = repository_class(sa_manager)
    repo.save_many({model, model2})

    results = [x for x in repo.find()]
    assert len(results) == 2

    repo.delete(1)
    results = [x for x in repo.find()]
    assert len(results) == 1
    assert results[0].model_id == 2
    assert results[0].name == "SomeoneElse"


def test_can_delete_by_instance(repository_class, model_class, sa_manager):
    model = model_class(
        model_id=1,
        name="Someone",
    )
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo = repository_class(sa_manager)
    repo.save_many({model, model2})

    results = [x for x in repo.find()]
    assert len(results) == 2

    repo.delete(model)
    results = [x for x in repo.find()]
    assert len(results) == 1
    assert results[0].model_id == 2
    assert results[0].name == "SomeoneElse"


def test_delete_inexistent_raises_exception(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager)

    results = [x for x in repo.find()]
    assert len(results) == 0

    with pytest.raises(Exception):
        repo.delete(4)
