import json
from pathlib import Path

current_dir = Path(__file__).resolve().parent.parent.parent

def read_json_file(file_path = current_dir / "data" / "restaurants.json"):

    with open(file_path, "r") as file:
        data = json.load(file)
    return data