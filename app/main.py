import json  
from fastapi import FastAPI, status
from app.services.restaurant_services import list_restaurants
from app.repositories.restaurant_repositories import update_json, read_json_file, update_restaurant
from app.schemas.restaurant import Restaurant

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

@app.post("/restaurants")
async def create_restaurant(NewRestaurant: Restaurant):
    new_restaurant = Restaurant(NewRestaurant)
    data = read_json_file()
    data.append(new_restaurant.model_dump())
    update_json(data)
    return {"message": "Restaurant created"}

@app.put("/restaurants/{restaurant_id}")
def update_restaurant_service(restaurant_id, updated_data):
    return update_restaurant(restaurant_id, updated_data)

    