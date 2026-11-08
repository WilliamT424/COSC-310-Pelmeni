import json
import os
import tempfile
from pathlib import Path
from app.repositories.json_storage import atomic_write_json


current_dir = Path(__file__).resolve().parent.parent.parent

def read_all_customers_json_file(file_path = current_dir / "data" / "customers.json"):
    with open(file_path, "r") as file:
        return json.load(file)

def read_customer_json_file(customer_id, file_path = current_dir / "data" / "customers.json"):

    with open(file_path, "r") as file:
        data = json.load(file)
        customer = [item for item in data if item["customerId"] == customer_id]

    return customer


def write_customer_json_file(customer_id, customer_data, file_path = current_dir / "data" / "customers.json"):
    with open(file_path, "r") as file:
        data = json.load(file)
        prev_data = [item for item in data if item["customerId"] == customer_id]
    if not prev_data:
        new_customer_data = [customer_data]
        atomic_write_json(new_customer_data, file_path)
    else:
        prev_data[0].update(customer_data)
        with open(file_path, "w") as file:
            json.dump(data, file)
    return True
