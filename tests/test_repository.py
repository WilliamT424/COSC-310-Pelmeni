import json

import pytest
from pydantic import ValidationError

from repositories.restaurant_repositories import read_json_file
from services.restaurant_services import list_restaurants
import services.restaurant_services as restaurant_services

SAMPLE = [
    {"id": 1, "name": "Alpha", "rating": 5, "cuisine": "A", "deliveryTime": 10},
    {"id": 2, "name": "Beta", "rating": 3, "cuisine": "B", "deliveryTime": 20},
]


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps(SAMPLE))
    return path


def test_read_json_file_returns_every_restaurant(data_file):
    data = read_json_file(data_file)
    assert len(data) == len(SAMPLE)


def test_read_json_file_preserves_restaurant_fields(data_file):
    data = read_json_file(data_file)
    alpha = next(r for r in data if r["id"] == 1)
    assert alpha["name"] == "Alpha"
    assert alpha["cuisine"] == "A"


def test_read_json_file_missing_file_raises_file_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(FileNotFoundError):
        read_json_file(missing_path)


def test_list_restaurants_rejects_invalid_restaurant_data(monkeypatch):
    invalid_data = [{"id": 1, "name": "Missing Fields"}]
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: invalid_data)

    with pytest.raises(ValidationError):
        list_restaurants()
