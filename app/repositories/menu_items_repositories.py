import json
from pathlib import Path

current_dir = Path(__file__).resolve().parent.parent.parent

def read_menu_json_file(restaurant_id, file_path = current_dir / "data" / "menu_items.json"):

    with open(file_path, "r") as file:

        data = json.load(file)
        restaurant_menu_items = [item for item in data if item["restaurant_id"] == restaurant_id]
    return restaurant_menu_items


def write_json_file_by_restaurant(restaurant_id, item_data, file_path = current_dir / "data" / "menu_items.json"):
    with open(file_path, "r") as file:
        data = json.load(file)
        prev_data = [item for item in data if item["restaurant_id"] == restaurant_id and item["id"] == item_data["id"]]
    if prev_data is None:
        new_menu_data = prev_data + [item_data]
        with open(file_path, "w") as file:
            json.dump(new_menu_data, file)
    else:
        prev_data[0].update(item_data)
        with open(file_path, "w") as file:
            json.dump(data, file)
    return True
