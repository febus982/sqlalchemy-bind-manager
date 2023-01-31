import pytest

from sqlalchemy_bind_manager import SortDirection
from sqlalchemy_bind_manager.exceptions import UnmappedProperty


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
    repo = repository_class(sa_manager.get_bind())
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
    repo = repository_class(sa_manager.get_bind())
    repo.save_many({model, model2, model3})

    results = [m for m in repo.find(search_params={"name": "Someone"})]
    assert len(results) == 1


def test_find_filtered_fails_if_invalid_filter(repository_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    with pytest.raises(UnmappedProperty):
        results = [m for m in repo.find(search_params={"somename": "Someone"})]


def test_find_ordered(repository_class, model_class, sa_manager):
    model = model_class(
        name="Abbott",
    )
    model2 = model_class(
        name="Costello",
    )
    repo = repository_class(sa_manager.get_bind())
    repo.save_many({model, model2})

    results = [m for m in repo.find(order_by=("name",))]
    assert results[0].name == "Abbott"
    assert results[1].name == "Costello"

    results2 = [m for m in repo.find(order_by=(("name", SortDirection.ASC),))]
    assert results2[0].name == "Abbott"
    assert results2[1].name == "Costello"

    results3 = [m for m in repo.find(order_by=(("name", SortDirection.DESC),))]
    assert results3[1].name == "Abbott"
    assert results3[0].name == "Costello"


def test_find_ordered_fails_if_invalid_column(repository_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())
    with pytest.raises(UnmappedProperty):
        results = [m for m in repo.find(order_by=("unexisting",))]
    with pytest.raises(UnmappedProperty):
        results = [m for m in repo.find(order_by=(("unexisting", SortDirection.DESC),))]
