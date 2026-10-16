import json 
from app.repositories.menu_items_repositories import write_json_file_by_restaurant, read_menu_json_file
from app.repositories.restaurant_repositories import read_json_file
from app.schemas.menu_item import MenuItem

def create_menu_item(restaurant_id, item_name, item_price, item_inventory):
    
    data = read_menu_json_file(restaurant_id)

    new_item = MenuItem(
        id = len(data) + 1,
        name = item_name,
        price = item_price,
        inventory = item_inventory,
        restaurant_id = restaurant_id,
        restaurant_name = read_json_file(restaurant_id).get("name")
    )

    return new_item

def add_to_menu(restaurant_id, menu_item: MenuItem):

    new_item = {
        "id": menu_item.id,
        "name": menu_item.name,
        "price": menu_item.price,
        "inventory": menu_item.inventory,
        "restaurant_id": menu_item.restaurant_id,
        "restaurant_name": menu_item.restaurant_name,
    }

    write_json_file_by_restaurant(restaurant_id, new_item)

def update_menu_item(restaurant_id, updates: dict):

    updated_item = {
        "id": updates.get("id"),
        "name": updates.get("name"),
        "price": updates.get("price"),
        "inventory": updates.get("inventory"),
        "restaurant_id": updates.get("restaurant_id"),
        "restaurant_name": updates.get("restaurant_name"),
    }

    write_json_file_by_restaurant(restaurant_id, updated_item)    