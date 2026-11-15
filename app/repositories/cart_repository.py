import json
from pathlib import Path
from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
CARTS_FILE = current_dir / "data" / "carts.json"

def read_carts_file():
    with open(CARTS_FILE, "r") as file:
        data = json.load(file)
    return data

def write_carts_file(data):
    atomic_write_json(data, CARTS_FILE, indent=2)

def get_cart(customer_id: int, restaurant_id: int):
    carts = read_carts_file()

    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            return cart

    return None

def generate_cart_id():
    carts = read_carts_file()
    if not carts:
        return 1
    return max(cart["id"] for cart in carts) + 1