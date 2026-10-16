from pydantic import BaseModel


class Restaurant(BaseModel):
    id: int
    name: str
    rating: float
    cuisine: str
    deliveryTime: int

class RestaurantUpdate(BaseModel):
    name: str | None = None
    rating: float | None = None
    cuisine: str | None = None
    deliveryTime: int | None = None