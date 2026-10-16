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



@pytest.fixture(scope="session", autouse=True)
def real_data_files_untouched():
    #Fails the run if any test writes to the committed data files
    import hashlib
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent.parent / "data"
    digest = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in data_dir.glob("*.json")}
    before = digest()
    yield
    assert digest() == before, "A test modified a file in data/; tests must use temp copies"
