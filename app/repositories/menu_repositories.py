import json
from pathlib import Path

from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
MENUS_FILE = current_dir / "data" / "menus.json"


def read_menus_file(file_path=None):
    # Resolved at call time so tests can point MENUS_FILE at a temp copy
    with open(file_path or MENUS_FILE, "r") as file:
        data = json.load(file)

    return data


def write_menus_file(data, file_path=None):
    atomic_write_json(data, file_path or MENUS_FILE, indent=2)
