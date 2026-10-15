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
