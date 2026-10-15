from pydantic import BaseModel


class menuItem(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available: bool


class menu(BaseModel):
    id: int
    restaurant_id: int
    name: str
    items: list[menuItem]
