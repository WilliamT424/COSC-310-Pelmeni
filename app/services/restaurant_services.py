import json

from fastapi import HTTPException 
from app.repositories.restaurant_repositories import add_restaurant, read_json_file, update_restaurant
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


def update_restaurant_service(restaurant_id, updated_data):
    restaurant = update_restaurant(restaurant_id, updated_data)

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return restaurant

def create_restaurant_service(new_restaurant):
    restaurants = list_restaurants()

    for restaurant in restaurants:
        if restaurant["id"] == new_restaurant.id:
            raise HTTPException(
                status_code=409,
                detail="Restaurant with this ID already exists"
            )
    return add_restaurant(new_restaurant)
