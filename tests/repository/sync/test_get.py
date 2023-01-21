import pytest


def test_get_returns_model(repository_class, model_class, sa_manager):
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

    result = repo.get(1)
    assert result.model_id == 1
    assert result.name == "Someone"
    assert isinstance(result, model_class)

def test_get_raises_exception_if_not_found(repository_class, sa_manager):
    repo = repository_class(sa_manager)

    with pytest.raises(Exception):
        repo.get(3)
