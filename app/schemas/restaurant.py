from pydantic import BaseModel


class Restaurant(BaseModel):
    id: int
    name: str
    rating: int
    cuisine: str
    deliveryTime: int