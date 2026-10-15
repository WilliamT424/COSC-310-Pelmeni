import json  
from fastapi import FastAPI, status, HTTPException
from app.services.restaurant_services import create_restaurant_service, list_restaurants, get_restaurant, update_restaurant_service
from app.services.menu_services import list_menus_for_restaurant
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

@app.get("/restaurants/{restaurant_id}") #get request to retrieve the details of a specific restaurant; 
async def restaurant_details(restaurant_id: int):
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found by id")
    return restaurant

@app.get("/restaurants/{restaurant_id}/menus")  #get request to view menus
async def get_restaurant_menus(restaurant_id: int):
    menus = list_menus_for_restaurant(restaurant_id)
    if not menus:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menus

@app.post("/restaurants", status_code=201,response_model=Restaurant,responses={409: {"description": "Restaurant ID already exists"}})
async def create_restaurant(new_restaurant: Restaurant):
    return create_restaurant_service(new_restaurant)

@app.patch( "/restaurants/{restaurant_id}",response_model=Restaurant,responses={404: {"description": "Restaurant not found"}})
def update_restaurant_route( restaurant_id: int, updates: RestaurantUpdate):
    updated_data = updates.model_dump(exclude_unset=True)

    return update_restaurant_service(restaurant_id, updated_data)

