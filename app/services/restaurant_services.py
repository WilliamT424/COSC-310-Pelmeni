import json 
from repositories.restaurant_repositories import read_json_file
from schemas.restaurant import Restaurant


def list_restaurants():

    data = read_json_file()
    for restaurant in data:
        restaurant_obj = Restaurant(**restaurant)
        print(restaurant_obj)
    return data