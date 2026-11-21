import json

import pytest
from pydantic import ValidationError

from repositories import restaurant_repositories
from schemas.restaurant import Restaurant
from repositories.restaurant_repositories import read_json_file
from services.restaurant_services import list_restaurants
import services.restaurant_services as restaurant_services

SAMPLE = [
    {"id": 1, "name": "Alpha", "rating": 5, "cuisine": "A", "deliveryTime": 10},
    {"id": 2, "name": "Beta", "rating": 3, "cuisine": "B", "deliveryTime": 20},
]


@pytest.fixture
def data_file(tmp_path):
    data_folder = tmp_path / "data"
    data_folder.mkdir()

    path = data_folder / "restaurants.json"
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


def test_update_json(data_file, monkeypatch):
    monkeypatch.setattr(restaurant_repositories, "RESTAURANTS_FILE", data_file)
    new_data = [{"id": 3, "name": "Gamma"}]
    restaurant_repositories.update_json(new_data)
    result = restaurant_repositories.read_json_file(data_file)

    assert result == new_data

def test_update_restaurant(monkeypatch):
    monkeypatch.setattr(restaurant_repositories, "read_json_file", lambda: SAMPLE.copy())
    monkeypatch.setattr(restaurant_repositories, "update_json", lambda data: None)
    result = restaurant_repositories.update_restaurant(1, {"name": "Updated Alpha"})

    assert result["name"] == "Updated Alpha"
    assert result["id"] == 1

def test_update_restaurant_not_found(monkeypatch):
    monkeypatch.setattr(restaurant_repositories, "read_json_file", lambda: SAMPLE.copy())
    result = restaurant_repositories.update_restaurant(999, {"name": "Unknown"})
    assert result is None

def test_add_restaurant(monkeypatch):
    monkeypatch.setattr(restaurant_repositories, "read_json_file", lambda: SAMPLE.copy())
    monkeypatch.setattr(restaurant_repositories, "update_json", lambda data: None)

    new_restaurant = Restaurant(
        id=3,
        name="Gamma",
        rating=4,
        cuisine="Italian",
        deliveryTime=30
    )

    result = restaurant_repositories.add_restaurant(new_restaurant)

    assert result.id == 3
    assert result.name == "Gamma"


