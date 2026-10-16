import app.services.menu_services as menu_services
from app.services.menu_services import get_menu_item, list_menu_items


def test_list_menu_items_returns_all_items(client):
    response = client.get("/restaurants/101/menus/1/items")
    assert response.status_code == 200
    assert [i["name"] for i in response.json()] == ["Test Burger", "Test Fries"]


def test_list_menu_items_have_expected_fields(client):
    item = client.get("/restaurants/101/menus/1/items").json()[0]
    assert item == {"id": 1, "name": "Test Burger", "description": "A sample burger",
                    "price": 9.99, "available": True}


def test_list_menu_items_unknown_restaurant_returns_404(client):
    assert client.get("/restaurants/999/menus/1/items").status_code == 404


def test_list_menu_items_unknown_menu_returns_404(client):
    assert client.get("/restaurants/101/menus/99/items").status_code == 404


def test_list_menu_items_menu_of_other_restaurant_returns_404(client, monkeypatch):
    # menu 1 belongs to restaurant 101, so it must not be reachable via 102
    assert client.get("/restaurants/102/menus/1/items").status_code == 404


def test_list_menu_items_invalid_id_returns_422(client):
    assert client.get("/restaurants/abc/menus/1/items").status_code == 422


def test_get_single_menu_item_returns_item(client):
    response = client.get("/restaurants/101/menus/1/items/2")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Fries"
    assert response.json()["available"] is False


def test_get_single_menu_item_unknown_item_returns_404(client):
    assert client.get("/restaurants/101/menus/1/items/99").status_code == 404


def test_get_single_menu_item_unknown_menu_returns_404(client):
    assert client.get("/restaurants/101/menus/99/items/1").status_code == 404


def test_menu_items_reject_unsupported_method(client):
    assert client.delete("/restaurants/101/menus/1/items").status_code == 405


def test_service_helpers(monkeypatch, sample_menus):
    monkeypatch.setattr(menu_services, "read_menus_file", lambda: sample_menus)
    assert len(list_menu_items(101, 1)) == 2
    assert list_menu_items(101, 5) is None
    assert get_menu_item(101, 1, 1)["name"] == "Test Burger"
    assert get_menu_item(101, 1, 7) is None
