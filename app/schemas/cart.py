from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    restaurant_id: int | None = None
    menu_id: int
    menu_item_id: int
    quantity: int = Field(gt=0)

class CartItem(BaseModel):
    menu_item_id: int
    menu_id: int
    name: str
    price: float
    quantity: int = Field(gt=0)

class Cart(BaseModel):
    id: int
    customer_id: int = Field(serialization_alias="customerId")
    restaurant_id: int
    items: list[CartItem] = Field(default_factory=list)
    subtotal: float | None = None
    total: float | None = None

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)