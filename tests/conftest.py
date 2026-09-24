import json

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repository
from app.repository import RestaurantRepository

SAMPLE_RESTAURANTS = [
    {"id": 101, "name": "Test Bistro", "rating": 4, "cuisine": "Test", "deliveryTime": 25},
    {"id": 102, "name": "Mock Diner", "rating": 5, "cuisine": "Test", "deliveryTime": 15},
]


@pytest.fixture
def sample_restaurants():
    return [dict(restaurant) for restaurant in SAMPLE_RESTAURANTS]


@pytest.fixture
def temp_data_file(tmp_path, sample_restaurants):
    data_file = tmp_path / "restaurants.json"
    data_file.write_text(json.dumps(sample_restaurants))
    return data_file


@pytest.fixture
def client(temp_data_file):
    app.dependency_overrides[get_repository] = lambda: RestaurantRepository(temp_data_file)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
