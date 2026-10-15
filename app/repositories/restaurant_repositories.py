import json
from pathlib import Path

current_dir = Path(__file__).resolve().parent.parent.parent

def read_json_file(file_path = current_dir / "data" / "restaurants.json"):

    with open(file_path, "r") as file:
        data = json.load(file)
    return data

def update_json(data):
    with open(current_dir / "data" / "restaurants.json", "w") as file:
        data = json.dump(data,file,indent=4)

def update_restaurant(restaurant_id, updated_data):
    restaurants = read_json_file()

    for restaurant in restaurants:
        if restaurant["id"] == restaurant_id:
            restaurant.update(updated_data)
            update_json(restaurants)
            return restaurant

    return None