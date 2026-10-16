import json  
from fastapi import FastAPI, status
from services.menu_services import add_to_menu, create_menu_item, update_menu_item
from services.restaurant_services import list_restaurants

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

@app.post("/restaurants/{restaurant_id}/menu")
async def add_item_to_menu(menu_id: int, item_name: str, item_price: float, item_inventory: int, available: bool, description: str):

    new_item = create_menu_item(menu_id, item_name, item_price, available, description)
    add_to_menu(menu_id, new_item)

    return {"message": "Menu item created successfully"}

@app.put("/menu/{item_id}") #update data
async def update_item_in_menu(menu_id: int, updates: dict):

    update_menu_item(menu_id, updates)

    return {"message": "Menu item updated successfully"}