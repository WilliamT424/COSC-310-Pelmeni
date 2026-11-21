import json
from app.repositories import order_repository


def test_get_order(tmp_path):
    orders_file = tmp_path / "orders.json"

    orders = [
        {
            "orderId": 1,
            "customerId": 10,
            "items": []
        },
        {
            "orderId": 2,
            "customerId": 20,
            "items": []
        }
    ]

    orders_file.write_text(json.dumps(orders))

    result = order_repository.get_order(2, orders_file)

    assert result["orderId"] == 2
    assert result["customerId"] == 20


def test_get_order_not_found(tmp_path):
    orders_file = tmp_path / "orders.json"
    orders_file.write_text("[]")

    result = order_repository.get_order(999, orders_file)

    assert result is None


def test_get_orders_by_customer(tmp_path):
    orders_file = tmp_path / "orders.json"

    orders = [
        {"orderId": 1, "customerId": 10},
        {"orderId": 2, "customerId": 20},
        {"orderId": 3, "customerId": 10}
    ]

    orders_file.write_text(json.dumps(orders))

    result = order_repository.get_orders_by_customer(10, orders_file)

    assert len(result) == 2
    assert result[0]["orderId"] == 1
    assert result[1]["orderId"] == 3


def test_generate_order_id(tmp_path):
    orders_file = tmp_path / "orders.json"

    orders = [
        {"orderId": 1, "customerId": 10},
        {"orderId": 5, "customerId": 20}
    ]

    orders_file.write_text(json.dumps(orders))

    result = order_repository.generate_order_id(orders_file)

    assert result == 6


def test_generate_order_id_empty_file(tmp_path):
    orders_file = tmp_path / "orders.json"
    orders_file.write_text("[]")

    result = order_repository.generate_order_id(orders_file)

    assert result == 1


def test_write_orders_file(tmp_path):
    orders_file = tmp_path / "orders.json"

    orders = [
        {"orderId": 1, "customerId": 10}
    ]

    order_repository.write_orders_file(orders, orders_file)

    saved_orders = json.loads(orders_file.read_text())

    assert saved_orders == orders