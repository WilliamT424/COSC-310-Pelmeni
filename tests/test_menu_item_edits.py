import json

import pytest

import app.services.menu_services as menu_services
from app.repositories.menu_repositories import read_menus_file, write_menus_file

MENUS = [
    {"id": 1, "restaurant_id": 101, "name": "Test Bistro Menu", "items": [
        {"id": 1, "name": "Test Burger", "description": "A sample burger", "price": 9.99, "available": True},
        {"id": 2, "name": "Test Fries", "description": "A sample side", "price": 3.99, "available": False},
    ]},
    {"id": 2, "restaurant_id": 102, "name": "Empty Menu", "items": []},
]
NEW_ITEM = {"name": "Soda", "description": "Cold", "price": 2.5, "available": True}


@pytest.fixture
def store(monkeypatch):
    """In-memory stand-in for menus.json so tests never touch the real data file."""
    data = json.loads(json.dumps(MENUS))
    monkeypatch.setattr(menu_services, "read_menus_file", lambda: json.loads(json.dumps(data)))
    monkeypatch.setattr(menu_services, "write_menus_file", lambda new: (data.clear(), data.extend(new)))
    return data


# --- POST -------------------------------------------------------------------

def test_add_item_returns_201_and_item(client, store):
    response = client.post("/restaurants/101/menus/1/items", json=NEW_ITEM)
    assert response.status_code == 201
    assert response.json() == {"id": 3, **NEW_ITEM}


def test_add_item_is_persisted(client, store):
    client.post("/restaurants/101/menus/1/items", json=NEW_ITEM)
    assert [i["name"] for i in store[0]["items"]] == ["Test Burger", "Test Fries", "Soda"]
    assert client.get("/restaurants/101/menus/1/items/3").json()["name"] == "Soda"


def test_add_item_to_empty_menu_gets_id_1(client, store):
    assert client.post("/restaurants/102/menus/2/items", json=NEW_ITEM).json()["id"] == 1


def test_add_item_defaults(client, store):
    response = client.post("/restaurants/101/menus/1/items", json={"name": "Water", "price": 0})
    assert response.json()["available"] is True
    assert response.json()["description"] == ""


def test_add_item_unknown_menu_returns_404(client, store):
    assert client.post("/restaurants/101/menus/99/items", json=NEW_ITEM).status_code == 404


def test_add_item_menu_of_other_restaurant_returns_404(client, store):
    assert client.post("/restaurants/102/menus/1/items", json=NEW_ITEM).status_code == 404


@pytest.mark.parametrize("body", [
    {"price": 1},                       # missing name
    {"name": "", "price": 1},           # empty name
    {"name": "X"},                      # missing price
    {"name": "X", "price": -1},         # negative price
    {"name": "X", "price": "abc"},      # non-numeric price
])
def test_add_item_invalid_body_returns_422(client, store, body):
    assert client.post("/restaurants/101/menus/1/items", json=body).status_code == 422
    assert len(store[0]["items"]) == 2


# --- PATCH ------------------------------------------------------------------

def test_update_item_changes_only_given_fields(client, store):
    response = client.patch("/restaurants/101/menus/1/items/1", json={"price": 12.5})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Test Burger", "description": "A sample burger",
                               "price": 12.5, "available": True}


def test_update_item_is_persisted(client, store):
    client.patch("/restaurants/101/menus/1/items/2", json={"available": True})
    assert store[0]["items"][1]["available"] is True


def test_update_item_cannot_change_id(client, store):
    client.patch("/restaurants/101/menus/1/items/1", json={"id": 99, "name": "Renamed"})
    assert store[0]["items"][0]["id"] == 1
    assert store[0]["items"][0]["name"] == "Renamed"


def test_update_unknown_item_returns_404(client, store):
    assert client.patch("/restaurants/101/menus/1/items/99", json={"price": 1}).status_code == 404


def test_update_unknown_menu_returns_404(client, store):
    assert client.patch("/restaurants/101/menus/99/items/1", json={"price": 1}).status_code == 404


@pytest.mark.parametrize("body", [{"price": -5}, {"name": ""}, {"available": "maybe"}])
def test_update_item_invalid_body_returns_422(client, store, body):
    assert client.patch("/restaurants/101/menus/1/items/1", json=body).status_code == 422


def test_old_flat_routes_are_gone(client, store):
    assert client.put("/menu/1", json={}).status_code == 404


# --- repository -------------------------------------------------------------

def test_write_menus_file_round_trips(tmp_path):
    path = tmp_path / "menus.json"
    write_menus_file(MENUS, path)
    assert read_menus_file(path) == MENUS
    assert list(tmp_path.iterdir()) == [path]  # no leftover temp files


def test_write_menus_file_failure_keeps_original(tmp_path):
    path = tmp_path / "menus.json"
    write_menus_file(MENUS, path)
    with pytest.raises(TypeError):
        write_menus_file([{"bad": object()}], path)
    assert read_menus_file(path) == MENUS
    assert list(tmp_path.iterdir()) == [path]
