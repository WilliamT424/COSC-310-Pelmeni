from pydantic import BaseModel, Field
from app.schemas.customer import Address


class OrderItem(BaseModel):
    menu_item_id: int
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    quantity: int = Field(gt=0)


class Order(BaseModel):
    orderId: int
    customerId: int
    deliveryAddress: Address
    items: list[OrderItem] = Field(default_factory=list)
    subtotal: float = Field(ge=0)
    total: float = Field(ge=0)

class OrdersResponse(BaseModel):
    orders: list[Order]