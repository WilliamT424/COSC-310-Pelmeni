from pydantic import BaseModel, Field

from app.schemas.cart import CartItem
from app.schemas.customer import Address


class Order(BaseModel):
    """An order created from a cart at checkout.

    Everything needed to understand the order later is copied in at checkout (item names and prices,
    restaurant name, delivery address), so editing the menu, restaurant or customer afterwards
    never changes order history.
    """
    orderId: int
    customerId: int
    restaurant_id: int
    restaurant_name: str
    deliveryAddress: Address
    items: list[CartItem]
    subtotal: float = Field(ge=0)
    total: float = Field(ge=0)
    status: str
    created_at: str = Field(description="UTC ISO-8601 timestamp of when the order was created")


class OrdersResponse(BaseModel):
    orders: list[Order]
