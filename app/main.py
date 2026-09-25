import json  
from fastapi import FastAPI, status
from app.services.restaurant_services import list_restaurants

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
