import json

import pytest

from app.repository import RestaurantRepository

SAMPLE = [
    {"id": 1, "name": "Alpha", "rating": 5, "cuisine": "A", "deliveryTime": 10},
    {"id": 2, "name": "Beta", "rating": 3, "cuisine": "B", "deliveryTime": 20},
]


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps(SAMPLE))
    return path


def test_get_all_returns_every_restaurant(data_file):
    repo = RestaurantRepository(data_file)
    assert len(repo.get_all()) == len(SAMPLE)


def test_get_all_preserves_restaurant_fields(data_file):
    repo = RestaurantRepository(data_file)
    alpha = next(r for r in repo.get_all() if r["id"] == 1)
    assert alpha["name"] == "Alpha"
    assert alpha["cuisine"] == "A"


def test_get_by_id_returns_matching_restaurant(data_file):
    repo = RestaurantRepository(data_file)
    assert repo.get_by_id(2)["name"] == "Beta"


def test_get_by_id_returns_none_for_unknown_id(data_file):
    repo = RestaurantRepository(data_file)
    assert repo.get_by_id(9999) is None


def test_loading_missing_file_raises_file_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    repo = RestaurantRepository(missing_path)

    with pytest.raises(FileNotFoundError):
        repo.get_all()
