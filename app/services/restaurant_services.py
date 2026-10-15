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