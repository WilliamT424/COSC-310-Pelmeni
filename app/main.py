import json  
from typing import Optional
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, status, HTTPException, Query
from app.services.restaurant_services import create_restaurant_service, list_restaurants, get_restaurant, search_restaurants, update_restaurant_service
from app.services.menu_services import list_menus_for_restaurant, list_menu_items, get_menu_item, add_menu_item, update_menu_item
from app.schemas.menu import menuItem, MenuItemCreate, MenuItemUpdate
from app.schemas.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to Pelmeni!"}

@app.get("/health")
async def health(status_code: int = status.HTTP_200_OK):
    return {"status": "healthy"}

@app.get("/restaurants")
async def get_restaurants():
    data = list_restaurants()
    return {"restaurants": data}

@app.get(
    "/restaurants/search",
    summary="Search and filter restaurants",
    description="Returns restaurants matching all provided filters. With no filters, returns every restaurant. "
                "An empty result is returned as an empty list with status 200.",
    responses={422: {"description": "Invalid filter value (e.g. non-numeric or negative)"}},
)
async def search_restaurants_route(
    name: Optional[str] = Query(None, description="Case-insensitive substring of the restaurant name"),
    cuisine: Optional[str] = Query(None, description="Case-insensitive substring of the cuisine"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating (0-5)"),
    max_delivery_time: Optional[int] = Query(None, ge=0, description="Maximum delivery time in minutes"),
):
    return {"restaurants": search_restaurants(name, cuisine, min_rating, max_delivery_time)}

@app.get("/restaurants/{restaurant_id}") #get request to retrieve the details of a specific restaurant; 
async def restaurant_details(restaurant_id: int):
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found by id")
    return restaurant

@app.get("/restaurants/{restaurant_id}/menus")  #get request to view menus
async def get_restaurant_menus(restaurant_id: int):
    if get_restaurant(restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return list_menus_for_restaurant(restaurant_id)

@app.get(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items",
    response_model=list[menuItem],
    summary="List menu items",
    description="Returns every item on the given menu of the given restaurant.",
    responses={404: {"description": "Menu not found for this restaurant"}},
)
async def get_menu_items(restaurant_id: int, menu_id: int):
    items = list_menu_items(restaurant_id, menu_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return items

@app.get(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}",
    response_model=menuItem,
    summary="Get a menu item",
    description="Returns a single item from the given menu of the given restaurant.",
    responses={404: {"description": "Menu or menu item not found"}},
)
async def get_single_menu_item(restaurant_id: int, menu_id: int, item_id: int):
    item = get_menu_item(restaurant_id, menu_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@app.post(
    "/restaurants",
    status_code=201,
    response_model=Restaurant,
    summary="Create a restaurant",
    description="Creates a restaurant and persists it. The id is assigned by the server.",
    responses={422: {"description": "Invalid restaurant data (missing field, rating outside 0-5, negative delivery time, empty name or cuisine)"}},
)
async def create_restaurant(new_restaurant: RestaurantCreate):
    return create_restaurant_service(new_restaurant)

@app.patch(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    summary="Update a restaurant",
    description="Updates only the provided fields of an existing restaurant. The id cannot be changed and provided fields cannot be null.",
    responses={404: {"description": "Restaurant not found"}, 422: {"description": "Invalid restaurant data"}},
)
def update_restaurant_route( restaurant_id: int, updates: RestaurantUpdate):
    updated_data = updates.model_dump(exclude_unset=True)

    return update_restaurant_service(restaurant_id, updated_data)

@app.post(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items",
    status_code=201,
    response_model=menuItem,
    summary="Add a menu item",
    description="Adds a new item to the given menu. The item id is assigned by the server.",
    responses={404: {"description": "Menu not found for this restaurant"}, 422: {"description": "Invalid item data"}},
)
async def add_item_to_menu(restaurant_id: int, menu_id: int, new_item: MenuItemCreate):
    item = add_menu_item(restaurant_id, menu_id, new_item)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return item

@app.patch(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}",
    response_model=menuItem,
    summary="Update a menu item",
    description="Updates only the provided fields of an existing menu item.",
    responses={404: {"description": "Menu or menu item not found"}, 422: {"description": "Invalid item data"}},
)
async def update_item_in_menu(restaurant_id: int, menu_id: int, item_id: int, updates: MenuItemUpdate):
    item = update_menu_item(restaurant_id, menu_id, item_id, updates)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

# Basic frontend, served from the same origin as the API (open http://127.0.0.1:8000/ui/)
app.mount("/ui", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="ui")
