import json
from pathlib import Path
from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
ORDERS_FILE = current_dir / "data" / "orders.json"


def read_orders_file(file_path=ORDERS_FILE):
    with open(file_path, "r") as file:
        return json.load(file)


def write_orders_file(data, file_path=ORDERS_FILE):
    atomic_write_json(data, file_path, indent=2)


def get_order(order_id, file_path=ORDERS_FILE):
    orders = read_orders_file(file_path)

    for order in orders:
        if order["orderId"] == order_id:
            return order

    return None


def get_orders_by_customer(customer_id, file_path=ORDERS_FILE):
    orders = read_orders_file(file_path)

    return [
        order for order in orders
        if order["customerId"] == customer_id
    ]
