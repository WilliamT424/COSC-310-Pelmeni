import json 
from app.repositories.restaurant_repositories import read_json_file
from app.schemas.restaurant import Restaurant


def list_restaurants():

    data = read_json_file()
    for restaurant in data:
        restaurant_obj = Restaurant(**restaurant)
        print(restaurant_obj)
    return data

def get_restaurant(restaurant_id: int):

    data = read_json_file()
    for restaurant in data:
        if restaurant["id"] == restaurant_id:
            return restaurant
    return None



def search_restaurants(name=None, cuisine=None, min_rating=None, max_delivery_time=None):
    """Return restaurants matching every provided filter (case-insensitive substring for name/cuisine)."""
    results = read_json_file()
    if name:
        results = [r for r in results if name.lower() in r["name"].lower()]
    if cuisine:
        results = [r for r in results if cuisine.lower() in r["cuisine"].lower()]
    if min_rating is not None:
        results = [r for r in results if r["rating"] >= min_rating]
    if max_delivery_time is not None:
        results = [r for r in results if r["deliveryTime"] <= max_delivery_time]
    return results
