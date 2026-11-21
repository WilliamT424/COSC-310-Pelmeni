from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace
import pytest
from app.services.checkout_services import CartNotFound, CustomerNotFound, InvalidCart, checkout


@pytest.fixture
def checkout_state(monkeypatch):
    state = {
        "customer": SimpleNamespace(
            customerId=7,
            status=True,
            deliveryAddress={
                "street": "123 Test Street",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1V 1V1",
                "country": "Canada",
            },
        ),
        "cart": {
            "id": 20,
            "customer_id": 7,
            "restaurant_id": 101,
            "items": [
                {
                    "menu_id": 3,
                    "menu_item_id": 5,
                    "name": "Old Pizza Name",
                    "price": 4.00,
                    "quantity": 2,
                }
            ],
        },
        "restaurant": {"id": 101, "name": "Test Bistro"},
        "menu_items": [
            {"id": 5, "name": "Fresh Pizza", "price": 12.50, "available": True}
        ],
        "orders": [],
        "saved": [],
        "cleared": [],
    }

    monkeypatch.setattr("app.services.checkout_services.retrieve_customer", lambda customer_id: state["customer"])
    monkeypatch.setattr("app.services.checkout_services.get_cart", lambda customer_id, restaurant_id: state["cart"])
    monkeypatch.setattr("app.services.checkout_services.get_restaurant", lambda restaurant_id: state["restaurant"])
    monkeypatch.setattr(
        "app.services.checkout_services.list_menu_items",
        lambda restaurant_id, menu_id: state["menu_items"],
    )
    monkeypatch.setattr("app.services.checkout_services.read_orders_file", lambda: deepcopy(state["orders"]))

    def fake_write(orders):
        state["orders"] = deepcopy(orders)
        state["saved"].append(deepcopy(orders))

    def fake_clear(customer_id, restaurant_id):
        state["cleared"].append((customer_id, restaurant_id))

    monkeypatch.setattr("app.services.checkout_services.write_orders_file", fake_write)
    monkeypatch.setattr("app.services.checkout_services.clear_cart", fake_clear)
    return state


def assert_no_side_effects(state):
    assert state["saved"] == []
    assert state["cleared"] == []


def test_checkout_creates_pending_order_with_current_prices(checkout_state):
    order = checkout(7, 101)

    assert order["orderId"] == 1
    assert order["customerId"] == 7
    assert order["restaurant_id"] == 101
    assert order["restaurant_name"] == "Test Bistro"
    assert order["deliveryAddress"] == checkout_state["customer"].deliveryAddress
    assert order["status"] == "pending"
    assert order["items"] == [
        {
            "menu_item_id": 5,
            "menu_id": 3,"name": "Fresh Pizza",
            "price": 12.50,
            "quantity": 2,
        }
    ]
    assert order["subtotal"] == 25.00
    assert order["total"] == 25.00
    assert datetime.fromisoformat(order["created_at"]).utcoffset().total_seconds() == 0
    assert checkout_state["orders"] == [order]
    assert checkout_state["cleared"] == [(7, 101)]


def test_checkout_uses_next_order_id(checkout_state):
    checkout_state["orders"] = [{"orderId": 4}, {"orderId": 9}]
    order = checkout(7, 101)
    assert order["orderId"] == 10
    assert len(checkout_state["orders"]) == 3


@pytest.mark.parametrize("customer", [None, SimpleNamespace(customerId=7, status=False)])
def test_checkout_rejects_missing_or_inactive_customer(checkout_state, customer):
    checkout_state["customer"] = customer
    with pytest.raises(CustomerNotFound):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


def test_checkout_rejects_missing_cart(checkout_state):
    checkout_state["cart"] = None
    with pytest.raises(CartNotFound):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


def test_checkout_rejects_missing_restaurant(checkout_state):
    checkout_state["restaurant"] = None
    with pytest.raises(InvalidCart, match="no longer exists"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


def test_checkout_rejects_empty_cart(checkout_state):
    checkout_state["cart"]["items"] = []
    with pytest.raises(InvalidCart, match="Cart is empty"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, "2"])
def test_checkout_rejects_bad_quantities(checkout_state, quantity):
    checkout_state["cart"]["items"][0]["quantity"] = quantity
    with pytest.raises(InvalidCart, match="Invalid quantity"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


def test_checkout_rejects_missing_menu_item(checkout_state):
    checkout_state["menu_items"] = []
    with pytest.raises(InvalidCart, match="not found"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)

def test_checkout_rejects_unavailable_menu_item(checkout_state):
    checkout_state["menu_items"][0]["available"] = False
    with pytest.raises(InvalidCart, match="not available"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)


def test_checkout_does_not_clear_cart_if_save_fails(checkout_state, monkeypatch):
    def failing_write(orders):
        raise OSError("simulated save failure")

    monkeypatch.setattr("app.services.checkout_services.write_orders_file", failing_write)
    with pytest.raises(OSError, match="simulated save failure"):
        checkout(7, 101)
    assert checkout_state["cleared"] == []
    assert checkout_state["orders"] == []


def test_reprice_items_validates_all_cart_lines(checkout_state):
    checkout_state["cart"]["items"].append(
        {"menu_id": 3, "menu_item_id": 99, "price": 1, "quantity": 1}
    )
    with pytest.raises(InvalidCart, match="99 not found"):
        checkout(7, 101)
    assert_no_side_effects(checkout_state)