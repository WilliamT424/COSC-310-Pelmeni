"""API contract tests for customer carts.

The cart implementation is not present yet. These tests define a REST contract
for it: carts are scoped to a customer, menu item prices come from the backend
catalog, and the cart response contains ``items``, ``subtotal`` and ``total``.
The menu fixture provides deterministic data for these tests so they do not
depend on a production catalog.
"""

from decimal import Decimal
from types import SimpleNamespace

import json
import pytest
from fastapi.testclient import TestClient

from main import app
import app.services.menu_services as menu_services
import app.services.restaurant_services as restaurant_services
import app.services.cart_services as cart_services
import app.repositories.cart_repository as cart_repository
from app.dependencies.dependencies import require_customer_ownership



@pytest.fixture
def sample_menu_catalog(sample_menus):
    """Copy the shared sample catalog and make both items orderable."""
    return [
        {
            **menu,
            "items": [dict(item, available=True) for item in menu["items"]],
        }
        for menu in sample_menus
    ]


@pytest.fixture
def sample_menu_items(sample_menu_catalog):
    return [
        {
            **item,
            "restaurant_id": menu["restaurant_id"],
            "menu_id": menu["id"],
        }
        for menu in sample_menu_catalog
        for item in menu["items"]
    ]


@pytest.fixture
def client(monkeypatch, tmp_path, sample_restaurants, sample_menu_catalog):
    """Use isolated sample data for cart API requests."""
    cart_file = tmp_path / "carts.json"
    cart_file.write_text("[]")

    def fake_customer_ownership(customer_id: int):
        return {"customerId": customer_id}

    monkeypatch.setitem(
        app.dependency_overrides,
        require_customer_ownership,
        fake_customer_ownership,
    )

    monkeypatch.setattr(
        restaurant_services, "read_json_file", lambda: sample_restaurants
    )
    monkeypatch.setattr(
        menu_services, "read_menus_file", lambda: sample_menu_catalog
    )
    monkeypatch.setattr(
        cart_services,
        "retrieve_customer",
        lambda customer_id: SimpleNamespace(id=customer_id, status=True),
    )
    monkeypatch.setattr(
        cart_services,
        "read_carts_file",
        lambda: json.loads(cart_file.read_text()),
    )

    monkeypatch.setattr(
        cart_services,
        "write_carts_file",
        lambda data: cart_file.write_text(json.dumps(data, indent=2)),
    )

    monkeypatch.setattr(
        cart_services,
        "generate_cart_id",
        lambda: max(
            (cart["id"] for cart in json.loads(cart_file.read_text())),
            default=0,
        ) + 1,
    )

    with TestClient(app) as test_client:
        yield test_client


def cart_url(customer_id):
    return f"/customers/{customer_id}/cart"


def item_url(customer_id, menu_item_id):
    return f"{cart_url(customer_id)}/items/{menu_item_id}"


def add_item(client, customer_id, menu_item, quantity):
    return client.post(
        f"{cart_url(customer_id)}/items",
        json={
            "restaurant_id": menu_item["restaurant_id"],
            "menu_id": menu_item["menu_id"],
            "menu_item_id": menu_item["id"],
            "quantity": quantity,
        },
    )


def test_create_or_retrieve_cart_returns_same_active_cart(client):
    customer_id = 501
    restaurant_id = 101

    created = client.post(
        cart_url(customer_id),
        params={"restaurant_id": restaurant_id},
    )
    retrieved = client.get(
        cart_url(customer_id),
        params={"restaurant_id": restaurant_id},
    )

    assert created.status_code in (200, 201)
    assert retrieved.status_code == 200
    assert created.json()["id"] == retrieved.json()["id"]
    assert created.json()["customerId"] == customer_id
    assert retrieved.json()["items"] == []


def test_add_menu_item_to_cart(client, sample_menu_items):
    customer_id = 502
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
)

    menu_item = sample_menu_items[0]
    response = add_item(
        client, customer_id, menu_item=menu_item, quantity=2
    )

    assert response.status_code in (200, 201)
    cart = response.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["menu_item_id"] == menu_item["id"]
    assert cart["items"][0]["quantity"] == 2


def test_add_same_menu_item_increases_its_quantity(client, sample_menu_items):
    customer_id = 503
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    menu_item = sample_menu_items[0]
    add_item(client, customer_id, menu_item=menu_item, quantity=1)

    response = add_item(client, customer_id, menu_item=menu_item, quantity=2)

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 3


def test_update_item_quantity(client, sample_menu_items):
    customer_id = 504
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    menu_item = sample_menu_items[0]
    add_item(client, customer_id, menu_item=menu_item, quantity=1)

    response = client.patch(
    item_url(customer_id, menu_item["id"]),
    params={
        "restaurant_id": menu_item["restaurant_id"],
        "menu_id": menu_item["menu_id"],
    },
    json={"quantity": 4},
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code == 200
    item = next(
        item for item in response.json()["items"]
        if item["menu_item_id"] == menu_item["id"]
    )
    assert item["quantity"] == 4


@pytest.mark.parametrize("quantity", [0, -1])
def test_update_rejects_non_positive_quantity(client, sample_menu_items, quantity):
    customer_id = 520 if quantity == 0 else 521
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    menu_item = sample_menu_items[0]
    add_item(client, customer_id, menu_item=menu_item, quantity=1)

    response = client.patch(
        item_url(customer_id, menu_item["id"]), json={"quantity": quantity}
    )

    assert response.status_code == 422


def test_remove_menu_item(client, sample_menu_items):
    customer_id = 507
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    first_item, second_item = sample_menu_items
    add_item(client, customer_id, menu_item=first_item, quantity=1)
    add_item(client, customer_id, menu_item=second_item, quantity=2)

    response = client.delete(
    item_url(customer_id, first_item["id"]),
    params={
        "restaurant_id": first_item["restaurant_id"],
        "menu_id": first_item["menu_id"],
    },
    )

    assert response.status_code in (200, 204)
    cart = client.get(
    cart_url(customer_id),
    params={"restaurant_id": first_item["restaurant_id"]},
    ).json()
    assert [item["menu_item_id"] for item in cart["items"]] == [second_item["id"]]


def test_clear_cart_preserves_cart_and_removes_all_items(client, sample_menu_items):
    customer_id = 508
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    first_item, second_item = sample_menu_items
    add_item(client, customer_id, menu_item=first_item, quantity=2)
    add_item(client, customer_id, menu_item=second_item, quantity=1)

    response = client.delete(
    cart_url(customer_id),
    params={"restaurant_id": first_item["restaurant_id"]},
    )

    assert response.status_code in (200, 204)
    cart = client.get(
    cart_url(customer_id),
    params={"restaurant_id": first_item["restaurant_id"]},
    ).json()
    assert cart["items"] == []
    assert Decimal(str(cart["subtotal"])) == Decimal("0.00")
    assert Decimal(str(cart["total"])) == Decimal("0.00")


def test_retrieve_cart_contents_and_backend_calculated_totals(
    client, sample_menu_items
):
    customer_id = 509
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    first_item, second_item = sample_menu_items
    add_item(client, customer_id, menu_item=first_item, quantity=2)
    add_item(client, customer_id, menu_item=second_item, quantity=3)

    response = client.get(
    cart_url(customer_id),
    params={"restaurant_id": first_item["restaurant_id"]},
    )

    assert response.status_code == 200
    cart = response.json()
    assert {item["menu_item_id"] for item in cart["items"]} == {
        first_item["id"], second_item["id"]
    }
    # The request contains IDs and quantities only. Values must reflect the
    # backend catalog prices, not prices supplied by the customer.
    expected_subtotal = (
        Decimal(str(first_item["price"])) * 2
        + Decimal(str(second_item["price"])) * 3
    )
    assert Decimal(str(cart["subtotal"])) == expected_subtotal
    assert Decimal(str(cart["total"])) == expected_subtotal


def test_add_item_does_not_accept_client_supplied_price(
    client, sample_menu_items
):
    customer_id = 510
    client.post(
    cart_url(customer_id),
    params={"restaurant_id": sample_menu_items[0]["restaurant_id"]},
    )
    menu_item = sample_menu_items[0]

    response = client.post(
        f"{cart_url(customer_id)}/items",
        json={
            "restaurant_id": menu_item["restaurant_id"],
            "menu_id": menu_item["menu_id"],
            "menu_item_id": menu_item["id"],
            "quantity": 1,
            "price": 0.01,
        },
    )

    assert response.status_code in (200, 201)
    cart = response.json()
    print(cart)
    item = next(
        item for item in cart["items"]
        if item["menu_item_id"] == menu_item["id"]
    )
    expected_price = Decimal(str(menu_item["price"]))
    assert Decimal(str(item["price"])) == expected_price
    assert Decimal(str(cart["subtotal"])) == expected_price
    assert Decimal(str(cart["total"])) == expected_price
