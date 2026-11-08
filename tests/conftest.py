import os
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-that-is-at-least-32-bytes-long")

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
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: sample_restaurants)
    monkeypatch.setattr(menu_services, "read_menus_file", lambda: sample_menus)
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session", autouse=True)
def real_data_files_untouched():
    import hashlib
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent.parent / "data"
    digest = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in data_dir.glob("*.json")}
    before = digest()
    yield
    assert digest() == before, "A test modified a file in data/; tests must use temp copies"

from auth_support import CASEY_EMAIL, MORGAN_EMAIL, bearer, sample_customers, token_for

@pytest.fixture
def isolated_users(tmp_path, monkeypatch):
    import functools
    import json
    import app.services.auth_services as auth_services
    import app.services.customer_services as customer_services
    import app.dependencies.dependencies as dependencies

    customers_file = tmp_path / "customers.json"
    customers_file.write_text(json.dumps(sample_customers()))
    for module, names in (
        (auth_services, ["read_all_customers_json_file"]),
        (dependencies, ["read_customer_json_file"]),
        (customer_services, ["read_all_customers_json_file", "read_customer_json_file", "write_customer_json_file"]),
    ):
        for name in names:
            monkeypatch.setattr(module, name, functools.partial(getattr(module, name), file_path=customers_file))
    yield customers_file

@pytest.fixture
def auth_client(tmp_path, monkeypatch, sample_restaurants, sample_menus, isolated_users):
    import json
    import app.repositories.restaurant_repositories as restaurant_repositories
    import app.repositories.menu_repositories as menu_repositories

    restaurants_file, menus_file = tmp_path / "restaurants.json", tmp_path / "menus.json"
    restaurants_file.write_text(json.dumps(sample_restaurants))
    menus_file.write_text(json.dumps(sample_menus))
    monkeypatch.setattr(restaurant_repositories, "RESTAURANTS_FILE", restaurants_file)
    monkeypatch.setattr(menu_repositories, "MENUS_FILE", menus_file)
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def customer_headers(auth_client):
    return bearer(token_for(auth_client, CASEY_EMAIL))

@pytest.fixture
def manager_headers(auth_client):
    return bearer(token_for(auth_client, MORGAN_EMAIL))