#THIS IS TEMPORARY FILE, DO NOT USE IT. IT WILL BE DELETED IN THE FUTURE.
import json
from pathlib import Path

from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
CARTS_FILE = current_dir / "data" / "carts.json"

ACTIVE = "active"
CLOSED = "closed"


def read_carts_file(file_path=None):
    with open(file_path or CARTS_FILE, "r") as file:
        return json.load(file)


def write_carts_file(data, file_path=None):
    atomic_write_json(data, file_path or CARTS_FILE, indent=2)


def get_active_cart(customer_id: int) -> dict | None:
    for cart in read_carts_file():
        if cart["customer_id"] == customer_id and cart["status"] == ACTIVE:
            return cart
    return None


def close_cart(cart_id: int) -> None:
    carts = read_carts_file()
    for cart in carts:
        if cart["id"] == cart_id:
            cart["status"] = CLOSED
            write_carts_file(carts)
            return
