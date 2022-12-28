import pytest

from sqlalchemy_bind_manager import UnmappedProperty


def test_find(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo = repository_class(sa_manager)
    repo.save_many({model, model2, model3})

    results = [m for m in repo.find()]
    assert len(results) == 3


def test_find_filtered(repository_class, model_class, sa_manager):
    model = model_class(
        name="Someone",
    )
    model2 = model_class(
        name="SomeoneElse",
    )
    model3 = model_class(
        name="StillSomeoneElse",
    )
    repo = repository_class(sa_manager)
    repo.save_many({model, model2, model3})

    results = [m for m in repo.find(name="Someone")]
    assert len(results) == 1


def test_find_filtered_fails_if_invalid_filter(repository_class, sa_manager):
    repo = repository_class(sa_manager)
    with pytest.raises(UnmappedProperty):
        results = [m for m in repo.find(somename="Someone")]
