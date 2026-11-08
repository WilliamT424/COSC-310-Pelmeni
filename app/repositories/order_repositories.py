#THIS IS TEMPORARY FILE, DO NOT USE IT. IT WILL BE DELETED IN THE FUTURE.

import json
from pathlib import Path

from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
ORDERS_FILE = current_dir / "data" / "orders.json"


def read_orders_file(file_path=None):
    # Resolved at call time so tests can point ORDERS_FILE at a temp copy
    with open(file_path or ORDERS_FILE, "r") as file:
        return json.load(file)


def write_orders_file(data, file_path=None):
    atomic_write_json(data, file_path or ORDERS_FILE, indent=2)
