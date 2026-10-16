from fastapi.testclient import TestClient
from app.main import app
from app.services import restaurant_services

client = TestClient(app)

SAMPLE = [
    {"id": 1, "name": "Alpha", "rating": 5, "cuisine": "Italian", "deliveryTime": 20}
]

def test_create_restaurant(monkeypatch):
    monkeypatch.setattr(restaurant_services, "list_restaurants", lambda: [])
    monkeypatch.setattr(restaurant_services, "add_restaurant", lambda r: r)

    new_restaurant = {
        "id": 2,
        "name": "Beta",
        "rating": 4,
        "cuisine": "Chinese",
        "deliveryTime": 30
    }

    response = client.post("/restaurants", json=new_restaurant)

    assert response.status_code == 201
    assert response.json()["name"] == "Beta"

def test_create_duplicate_id(monkeypatch):
    monkeypatch.setattr(restaurant_services, "list_restaurants", lambda: SAMPLE)

    new_restaurant = {
        "id": 1,
        "name": "Beta",
        "rating": 4,
        "cuisine": "Chinese",
        "deliveryTime": 30
    }

    response = client.post("/restaurants", json=new_restaurant)

    assert response.status_code == 409

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

