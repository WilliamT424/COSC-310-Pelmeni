from pydantic import BaseModel, Field


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


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    price: float = Field(ge=0)
    available: bool = True


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    available: bool | None = None
