from app.repositories.restaurant_repositories import add_restaurant, read_json_file, update_restaurant
from app.schemas.restaurant import Restaurant, RestaurantCreate


def list_restaurants() -> list[dict]:
    """All restaurants. Raises pydantic.ValidationError if the stored data is malformed."""
    data = read_json_file()
    for restaurant in data:
        Restaurant(**restaurant)
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


def update_restaurant_service(restaurant_id: int, updated_data: dict) -> dict | None:
    """Apply the provided fields to a restaurant. Returns None if it doesn't exist."""
    return update_restaurant(restaurant_id, updated_data)


def create_restaurant_service(new_restaurant: RestaurantCreate) -> Restaurant:
    """Store a new restaurant under the next free id (ids are never reused or client-chosen)."""
    next_id = max((r["id"] for r in read_json_file()), default=0) + 1
    return add_restaurant(Restaurant(id=next_id, **new_restaurant.model_dump()))
