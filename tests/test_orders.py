"""API contract tests for orders and historical order snapshots.

The order implementation is not present yet. These tests follow the existing
collection/detail REST pattern and use only isolated sample customer, restaurant,
and menu data. Creating an order snapshots the selected menu item details and
delivery address; later catalog changes must not rewrite that history.
"""

from decimal import Decimal
from itertools import count

import pytest
from fastapi.testclient import TestClient

import main as api_module
import app.services.menu_services as menu_services
import app.services.restaurant_services as restaurant_services
from main import app
from schemas.customer import Address, Customer

_CUSTOMER_IDS = count(600)


@pytest.fixture
def sample_menu_catalog(sample_menus):
    # Copy nested item data so changing the catalog in a test cannot touch shared
    # fixtures or the committed data/menus.json file.
    return [
        {
            **menu,
            "items": [dict(item, available=True) for item in menu["items"]],
        }
        for menu in sample_menus
    ]


@pytest.fixture
def sample_customer():
    return Customer(
        customerId=next(_CUSTOMER_IDS),
        name="Order Test Customer",
        email="order-test@example.com",
        deliveryAddress=Address(
            street="100 Sample Street",
            city="Kelowna",
            province="BC",
            postal_code="V1Y 1A1",
            country="Canada",
        ),
        status=True,
    )


@pytest.fixture
def second_sample_customer(sample_customer):
    return sample_customer.model_copy(
        update={
            "customerId": sample_customer.customerId + 1,
            "email": "second-order-test@example.com",
        }
    )


@pytest.fixture
def client(
    monkeypatch,
    sample_restaurants,
    sample_menu_catalog,
    sample_customer,
    second_sample_customer,
):
    monkeypatch.setattr(
        restaurant_services, "read_json_file", lambda: sample_restaurants
    )
    monkeypatch.setattr(
        menu_services, "read_menus_file", lambda: sample_menu_catalog
    )
    monkeypatch.setattr(
        api_module,
        "retrieve_customer",
        lambda customer_id: {
            customer.customerId: customer
            for customer in (sample_customer, second_sample_customer)
        }.get(customer_id),
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_order_request(sample_customer, sample_menu_catalog):
    menu = sample_menu_catalog[0]
    item = menu["items"][0]
    return {
        "customerId": sample_customer.customerId,
        "deliveryAddress": sample_customer.deliveryAddress.model_dump(),
        "items": [
            {
                "restaurant_id": menu["restaurant_id"],
                "menu_id": menu["id"],
                "menu_item_id": item["id"],
                "quantity": 2,
            }
        ],
    }


def place_order(client, order_request):
    return client.post("/orders", json=order_request)


def test_retrieve_individual_order(client, sample_order_request, sample_menu_catalog):
    created = place_order(client, sample_order_request)
    assert created.status_code == 201
    order_id = created.json()["orderId"]

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == 200
    order = response.json()
    assert order["orderId"] == order_id
    assert order["customerId"] == sample_order_request["customerId"]
    assert order["deliveryAddress"] == sample_order_request["deliveryAddress"]
    item = sample_menu_catalog[0]["items"][0]
    assert order["items"] == [
        {
            "menu_item_id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": 2,
        }
    ]
    assert Decimal(str(order["subtotal"])) == Decimal(str(item["price"])) * 2
    assert Decimal(str(order["total"])) == Decimal(str(item["price"])) * 2


def test_retrieving_unknown_order_returns_404(client):
    response = client.get("/orders/999999")

    assert response.status_code == 404


def test_retrieve_orders_for_customer_returns_only_that_customers_orders(
    client, sample_order_request, second_sample_customer
):
    first = place_order(client, sample_order_request)
    second_request = {
        **sample_order_request,
        "customerId": second_sample_customer.customerId,
    }
    second = place_order(client, second_request)
    assert first.status_code == second.status_code == 201

    response = client.get(
        f"/customers/{sample_order_request['customerId']}/orders"
    )

    assert response.status_code == 200
    orders = response.json()["orders"]
    assert [order["orderId"] for order in orders] == [first.json()["orderId"]]
    assert all(
        order["customerId"] == sample_order_request["customerId"]
        for order in orders
    )


def test_order_keeps_original_item_and_delivery_details_after_catalog_changes(
    client, sample_order_request, sample_menu_catalog, sample_customer
):
    created = place_order(client, sample_order_request)
    assert created.status_code == 201
    order_id = created.json()["orderId"]
    original_item = dict(sample_menu_catalog[0]["items"][0])
    original_address = sample_order_request["deliveryAddress"].copy()

    # Simulate later edits to current source data. The order must remain a
    # snapshot of what was selected when it was placed.
    sample_menu_catalog[0]["items"][0]["name"] = "Renamed Current Dish"
    sample_menu_catalog[0]["items"][0]["price"] = 99.99
    sample_customer.deliveryAddress.street = "200 New Sample Street"

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == 200
    order = response.json()
    assert order["deliveryAddress"] == original_address
    assert order["items"][0]["name"] == original_item["name"]
    assert Decimal(str(order["items"][0]["price"])) == Decimal(
        str(original_item["price"])
    )
    assert Decimal(str(order["subtotal"])) == Decimal(str(original_item["price"])) * 2
    assert Decimal(str(order["total"])) == Decimal(str(original_item["price"])) * 2
