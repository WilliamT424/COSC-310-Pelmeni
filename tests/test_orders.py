"""API contract tests for orders and historical order snapshots.

The order implementation is not present yet. These tests follow the existing
collection/detail REST pattern and use only isolated sample customer, restaurant,
and menu data. Creating an order snapshots the selected menu item details and
delivery address; later catalog changes must not rewrite that history.
"""

from itertools import count

import pytest
from fastapi.testclient import TestClient

import main as api_module
from app.repositories import menu_repositories
import app.services.restaurant_services as restaurant_services
from main import app
from schemas.customer import Address, Customer
import app.services.order_services as order_services
from app.dependencies.dependencies import get_current_user

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
def sample_orders():
    return [
        {
            "orderId": 1,
            "customerId": 600,
            "restaurant_id": 1,
            "restaurant_name": "Zakura",
            "deliveryAddress": {
                "street": "100 Sample Street",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1",
                "country": "Canada",
            },
            "items": [],
            "subtotal": 10.0,
            "total": 10.0,
            "status": "pending",
            "created_at": "2026-11-26T00:00:00+00:00",
        }
    ]


@pytest.fixture
def client(
    monkeypatch,
    sample_restaurants,
    sample_menu_catalog,
    sample_customer,
    second_sample_customer,
    sample_orders,
):
    monkeypatch.setattr(
        restaurant_services, "read_json_file", lambda: sample_restaurants
    )
    monkeypatch.setattr(
        menu_repositories, "read_menus_file", lambda: sample_menu_catalog
    )
    monkeypatch.setattr(
        api_module,
        "retrieve_customer",
        lambda customer_id: {
            customer.customerId: customer
            for customer in (sample_customer, second_sample_customer)
        }.get(customer_id),
    )

    monkeypatch.setattr(
        order_services, "read_orders_file", lambda: sample_orders
    )
    monkeypatch.setattr(
        order_services, "write_orders_file", lambda orders: sample_orders.__setitem__(slice(None), orders)
    )

    monkeypatch.setattr(
        order_services, "get_order", lambda order_id: next(
            (order for order in sample_orders if order["orderId"] == order_id), None
        )
    )

    app.dependency_overrides[get_current_user] = lambda: sample_customer

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_current_user, None)


def test_retrieving_unknown_order_returns_404(client):
    response = client.get("/orders/999999")

    assert response.status_code == 404

def test_updating_order_status(client):
    response = client.patch("/orders/1/status?new_status=confirmed")

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

def test_cancelling_pending_order(client):
    response = client.patch("/orders/1/status?new_status=cancelled")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["orderId"] == 1

def test_cancelling_preparing_order_returns_409(client):
    client.patch("/orders/1/status?new_status=confirmed")
    client.patch("/orders/1/status?new_status=preparing")

    response = client.patch("/orders/1/status?new_status=cancelled")

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot transition order from 'preparing' to 'cancelled'"


def test_invalid_order_status_transition_returns_409(client):
    client.patch("/orders/1/status?new_status=confirmed")

    response = client.patch("/orders/1/status?new_status=delivered")

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot transition order from 'confirmed' to 'delivered'"


def test_updating_unknown_order_status_returns_404(client):
    response = client.patch("/orders/999999/status?new_status=confirmed")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order 999999 not found"

def test_cancelled_order_remains_retrievable(client):
    client.patch("/orders/1/status?new_status=cancelled")

    response = client.get("/orders/1")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["orderId"] == 1
    assert response.json()["customerId"] == 600

def test_delivered_order_remains_retrievable(client):
    client.patch("/orders/1/status?new_status=confirmed")
    client.patch("/orders/1/status?new_status=preparing")
    client.patch("/orders/1/status?new_status=ready")
    client.patch("/orders/1/status?new_status=out_for_delivery")
    client.patch("/orders/1/status?new_status=delivered")

    response = client.get("/orders/1")

    assert response.status_code == 200
    assert response.json()["status"] == "delivered"
    assert response.json()["orderId"] == 1
    assert response.json()["customerId"] == 600