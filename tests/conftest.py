import pytest
from fastapi.testclient import TestClient

import services.restaurant_services as restaurant_services
from app.main import app

SAMPLE_RESTAURANTS = [
    {"id": 101, "name": "Test Bistro", "rating": 4, "cuisine": "Test", "deliveryTime": 25},
    {"id": 102, "name": "Mock Diner", "rating": 5, "cuisine": "Test", "deliveryTime": 15},
]


@pytest.fixture
def sample_restaurants():
    return [dict(restaurant) for restaurant in SAMPLE_RESTAURANTS]


@pytest.fixture
def client(monkeypatch, sample_restaurants):
    #TestClient wired to isolated sample data instead of the committed dataset.
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: sample_restaurants)
    with TestClient(app) as test_client:
        yield test_client
