import pytest
from sqlalchemy import select


def test_can_delete_by_instance(repository_class, model_class, sa_manager):
    model = model_class(
        model_id=1,
        name="Someone",
    )
    model2 = model_class(
        model_id=2,
        name="SomeoneElse",
    )
    repo = repository_class(sa_manager.get_bind())
    repo.save_many({model, model2})

    results = [x for x in repo.find()]
    assert len(results) == 2

    repo.delete(model)
    results = [x for x in repo.find()]
    assert len(results) == 1
    assert results[0].model_id == 2
    assert results[0].name == "SomeoneElse"


def test_delete_inexistent_raises_exception(repository_class, model_class, sa_manager):
    repo = repository_class(sa_manager.get_bind())

    results = [x for x in repo.find()]
    assert len(results) == 0

    with pytest.raises(Exception):
        repo.delete(4)

    with pytest.raises(Exception):
        repo.delete(
            model_class(
                model_id=823,
                name="Someone",
            )
        )


def test_relationships_are_respected(
    related_repository_class, related_model_classes, sa_manager
):
    parent = related_model_classes[0](
        name="A Parent",
    )
    child = related_model_classes[1](name="A Child")
    child2 = related_model_classes[1](name="Another Child")
    parent.children.append(child)
    parent.children.append(child2)
    repo = related_repository_class(sa_manager.get_bind())
    repo.save(parent)

    retrieved_parent = repo.get(parent.parent_model_id)
    assert len(retrieved_parent.children) == 2

    repo.delete(retrieved_parent)

    with repo._get_session() as session:
        result = [
            x for x in session.execute(select(related_model_classes[1])).scalars()
        ]
        assert len(result) == 0
