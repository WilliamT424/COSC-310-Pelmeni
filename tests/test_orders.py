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


def test_retrieving_unknown_order_returns_404(client):
    response = client.get("/orders/999999")

    assert response.status_code == 404
