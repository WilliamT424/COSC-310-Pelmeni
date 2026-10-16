import json
from pathlib import Path
from app.schemas.restaurant import Restaurant
import app.repositories.restaurant_repositories as restaurant_repositories

current_dir = Path(__file__).resolve().parent.parent.parent
RESTAURANTS_FILE = current_dir / "data" / "restaurants.json"

def read_json_file(file_path = None):
    # Resolved at call time so tests can point RESTAURANTS_FILE at a temp copy
    with open(file_path or RESTAURANTS_FILE, "r") as file:
        data = json.load(file)
    return data

def update_json(data, file_path = None):
    with open(file_path or RESTAURANTS_FILE, "w") as file:
        json.dump(data,file,indent=4)

def update_restaurant(restaurant_id, updated_data):
    restaurants = read_json_file()
 
    for restaurant in restaurants:
        if restaurant["id"] == restaurant_id:
            restaurant.update(updated_data)
            update_json(restaurants)
            return restaurant

    return None

def add_restaurant(new_restaurant: Restaurant):
        data = read_json_file()
        data.append(new_restaurant.model_dump())
        update_json(data)

        return new_restaurant

