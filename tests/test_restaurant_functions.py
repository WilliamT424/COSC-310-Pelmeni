import json

import pytest
from pydantic import ValidationError

from repositories.restaurant_repositories import read_json_file
from services.restaurant_services import list_restaurants
import services.restaurant_services as restaurant_services

def test_restaurant_create():
    # Test creating a restaurant with valid data
    valid_data = {
        "id": 3,
        "name": "Buster's Bistro",
        "rating": 4,
        "cuisine": "UK",
        "deliveryTime": 15
    }
    new_restaurant = restaurant_services.create_restaurant(**valid_data) #check actual name
    assert new_restaurant.id == valid_data["id"]
    assert new_restaurant.name == valid_data["name"]
    assert new_restaurant.cuisine == valid_data["cuisine"]

def test_restaurant_create_invalid_data():

    invalid_data = {
        "id": 4,
        "name": "Delta"
    }
    with pytest.raises(ValidationError):
        restaurant_services.create_restaurant(**invalid_data) #check actual name

def test_restaurant_update():
    existing_restaurant = restaurant_services.create_restaurant(
        id=5,
        name="Michelin Madness",
        rating=3,
        cuisine="UK",
        deliveryTime=20
    )
    updates = {
        "name": "Michelin's Madness",
        "rating": 4
    }
    updated_restaurant = restaurant_services.update_restaurant(existing_restaurant.id, updates)

    assert updated_restaurant.name == updates["name"]
    assert updated_restaurant.rating == updates["rating"]

def test_restaurant_update_invalid_data():

    existing_restaurant = restaurant_services.create_restaurant(
        id=6,
        name="Parlour",
        rating=2,
        cuisine="Ice Cream",
        deliveryTime=30
    )
    invalid_updates = {
        "name": 123,  
        "rating": "high" 
    }
    with pytest.raises(ValidationError):
        restaurant_services.update_restaurant(existing_restaurant.id, invalid_updates)