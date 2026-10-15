import pytest
from fastapi.testclient import TestClient

import app.services.restaurant_services as restaurant_services
import app.services.menu_services as menu_services
from app.main import app

SAMPLE_RESTAURANTS = [
    {"id": 101, "name": "Test Bistro", "rating": 4, "cuisine": "Test", "deliveryTime": 25},
    {"id": 102, "name": "Mock Diner", "rating": 5, "cuisine": "Test", "deliveryTime": 15},
]

SAMPLE_MENUS = [
    {"id": 1, "restaurant_id": 101, "name": "Test Bistro Menu", "items": 
     [
        {"id": 1, "name": "Test Burger", "description": "A sample burger", "price": 9.99, "available": True},
        {"id": 2, "name": "Test Fries", "description": "A sample side", "price": 3.99, "available": False}
     ]
    }
]


@pytest.fixture
def sample_restaurants():
    return [dict(restaurant) for restaurant in SAMPLE_RESTAURANTS]

@pytest.fixture
def sample_menus():
    return [dict(menu) for menu in SAMPLE_MENUS]


@pytest.fixture
def client(monkeypatch, sample_restaurants, sample_menus):
    #TestClient wired to isolated sample data instead of the committed dataset
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: sample_restaurants)
    monkeypatch.setattr(menu_services, "read_menus_file", lambda: sample_menus)
    with TestClient(app) as test_client:
        yield test_client

