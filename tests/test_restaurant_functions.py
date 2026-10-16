import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import restaurant_services

client = TestClient(app)

SAMPLE = [
    {"id": 1, "name": "Alpha", "rating": 5, "cuisine": "Italian", "deliveryTime": 20}
]

def test_create_restaurant(monkeypatch):
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: [])
    monkeypatch.setattr(restaurant_services, "add_restaurant", lambda r: r)

    new_restaurant = {
        "name": "Beta",
        "rating": 4,
        "cuisine": "Chinese",
        "deliveryTime": 30
    }

    response = client.post("/restaurants", json=new_restaurant)

    assert response.status_code == 201
    assert response.json()["name"] == "Beta"
    assert response.json()["id"] == 1


def test_create_assigns_next_free_id_and_ignores_client_id(monkeypatch):
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: SAMPLE)
    monkeypatch.setattr(restaurant_services, "add_restaurant", lambda r: r)

    new_restaurant = {"id": 1, "name": "Beta", "rating": 4, "cuisine": "Chinese", "deliveryTime": 30}
    response = client.post("/restaurants", json=new_restaurant)

    assert response.status_code == 201
    assert response.json()["id"] == 2

def test_create_missing_fields():
    new_restaurant = {"id": 2,"name": "Beta" }
    response = client.post("/restaurants", json=new_restaurant)

    assert response.status_code == 422

def test_update_restaurant(monkeypatch):
    monkeypatch.setattr(restaurant_services,"update_restaurant",lambda id, data: {**SAMPLE[0], **data} )
    response = client.patch("/restaurants/1",json={"name": "Updated Alpha"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Alpha"


def test_update_restaurant_not_found(monkeypatch):
    monkeypatch.setattr( restaurant_services, "update_restaurant",lambda id, data: None )
    response = client.patch("/restaurants/999",json={"name": "Unknown"} )

    assert response.status_code == 404


def test_update_only_name(monkeypatch):
    monkeypatch.setattr(restaurant_services,"update_restaurant", lambda id, data: {**SAMPLE[0], **data})
    response = client.patch( "/restaurants/1", json={"name": "New Name"})

    assert response.status_code == 200
    assert response.json()["rating"] == 5
    assert response.json()["name"] == "New Name"



VALID = {"name": "Beta", "rating": 4, "cuisine": "Chinese", "deliveryTime": 30}


@pytest.mark.parametrize("change", [
    {"rating": 5.1}, {"rating": -1}, {"deliveryTime": -5},
    {"name": ""}, {"cuisine": ""}, {"name": None}, {"rating": "abc"},
])
def test_create_rejects_invalid_values(change):
    response = client.post("/restaurants", json={**VALID, **change})
    assert response.status_code == 422


@pytest.mark.parametrize("update", [
    {"name": None}, {"rating": None}, {"cuisine": None}, {"deliveryTime": None},
    {"rating": 6}, {"rating": -0.5}, {"deliveryTime": -1}, {"name": ""}, {"cuisine": ""},
])
def test_update_rejects_null_and_invalid_values(monkeypatch, update):
    called = []
    monkeypatch.setattr(restaurant_services, "update_restaurant", lambda id, data: called.append(data))
    response = client.patch("/restaurants/1", json=update)

    assert response.status_code == 422
    assert called == []


def test_update_accepts_decimal_rating(monkeypatch):
    monkeypatch.setattr(restaurant_services, "update_restaurant", lambda id, data: {**SAMPLE[0], **data})
    response = client.patch("/restaurants/1", json={"rating": 3.5})

    assert response.status_code == 200
    assert response.json()["rating"] == 3.5
