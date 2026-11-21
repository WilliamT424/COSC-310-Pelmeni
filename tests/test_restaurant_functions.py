import pytest
from pydantic import ValidationError

from app.schemas.restaurant import RestaurantCreate, Restaurant
import app.repositories.restaurant_repositories as restaurant_repositories
import services.restaurant_services as restaurant_services


@pytest.fixture
def restaurant_data(monkeypatch, tmp_path):
    file_path = tmp_path / "restaurants.json"
    file_path.write_text("[]")

    monkeypatch.setattr(
        restaurant_repositories,
        "RESTAURANTS_FILE",
        file_path
    )


def test_restaurant_create(restaurant_data):
    valid_data = {
        "name": "Buster's Bistro",
        "rating": 4,
        "cuisine": "UK",
        "deliveryTime": 15
    }

    new_restaurant = restaurant_services.create_restaurant_service(
        RestaurantCreate(**valid_data)
    )

    assert new_restaurant.id == 1
    assert new_restaurant.name == valid_data["name"]
    assert new_restaurant.cuisine == valid_data["cuisine"]
    assert new_restaurant.rating == valid_data["rating"]
    assert new_restaurant.deliveryTime == valid_data["deliveryTime"]


def test_restaurant_create_invalid_data():
    invalid_data = {
        "name": "Delta"
    }

    with pytest.raises(ValidationError):
        RestaurantCreate(**invalid_data)


def test_restaurant_create_auto_increment(restaurant_data):
    restaurant1 = restaurant_services.create_restaurant_service(
        RestaurantCreate(
            name="Restaurant 1",
            rating=3,
            cuisine="Italian",
            deliveryTime=20
        )
    )

    restaurant2 = restaurant_services.create_restaurant_service(
        RestaurantCreate(
            name="Restaurant 2",
            rating=4,
            cuisine="Japanese",
            deliveryTime=15
        )
    )

    assert restaurant1.id == 1
    assert restaurant2.id == 2


def test_restaurant_update(restaurant_data):
    existing_restaurant = restaurant_services.create_restaurant_service(
        RestaurantCreate(
            name="Michelin Madness",
            rating=3,
            cuisine="UK",
            deliveryTime=20
        )
    )

    updates = {
        "name": "Michelin's Madness",
        "rating": 4
    }

    updated_restaurant = restaurant_services.update_restaurant_service(
        existing_restaurant.id,
        updates
    )

    assert updated_restaurant["name"] == updates["name"]
    assert updated_restaurant["rating"] == updates["rating"]


def test_restaurant_update_invalid_data(restaurant_data):
    existing_restaurant = restaurant_services.create_restaurant_service(
        RestaurantCreate(
            name="Parlour",
            rating=2,
            cuisine="Ice Cream",
            deliveryTime=30
        )
    )

    invalid_updates = {
        "name": 123,
        "rating": "high"
    }

    with pytest.raises(ValidationError):
        Restaurant(
            **{
                **existing_restaurant.model_dump(),
                **invalid_updates
            }
        )