import json  
from fastapi import FastAPI, status
from services.menu_services import add_to_menu, create_menu_item, update_menu_item
from services.restaurant_services import list_restaurants
from typing import Optional
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, status, HTTPException, Query
from app.services.restaurant_services import create_restaurant_service, list_restaurants, get_restaurant, search_restaurants, update_restaurant_service
from app.services.menu_services import list_menus_for_restaurant, list_menu_items, get_menu_item
from app.schemas.menu import menuItem
from app.schemas.restaurant import Restaurant, RestaurantUpdate

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

@app.get("/docs")
async def get_docs():
    return {"message": "Documentation for Pelmeni API"}
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
    min_rating: Optional[int] = Query(None, ge=0, le=5, description="Minimum rating (0-5)"),
    max_delivery_time: Optional[int] = Query(None, ge=0, description="Maximum delivery time in minutes"),
):
    return {"restaurants": search_restaurants(name, cuisine, min_rating, max_delivery_time)}

@app.get("/restaurants/{restaurant_id}") #get request to retrieve the details of a specific restaurant; 
async def restaurant_details(restaurant_id: int):
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found by id")
    return restaurant

@app.post("/restaurants/{restaurant_id}/menu")
async def add_item_to_menu(menu_id: int, item_name: str, item_price: float, item_inventory: int, available: bool, description: str):

    new_item = create_menu_item(menu_id, item_name, item_price, available, description)
    add_to_menu(menu_id, new_item)

    return {"message": "Menu item created successfully"}

@app.put("/menu/{item_id}") #update data
async def update_item_in_menu(menu_id: int, updates: dict):

    update_menu_item(menu_id, updates)

    return {"message": "Menu item updated successfully"}
# Basic frontend, served from the same origin as the API (open http://127.0.0.1:8000/ui/)
app.mount("/ui", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="ui")
