#THIS IS TEMPORARY FILE, DO NOT USE IT. IT WILL BE DELETED IN THE FUTURE.

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """A line of an order. Name and price are copied from the menu at checkout so the order
    stays accurate even if the menu item is later renamed, repriced or removed."""
    menu_id: int
    menu_item_id: int
    name: str
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=1)
    line_total: float = Field(ge=0)


class Order(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    restaurant_name: str
    items: list[OrderItem]
    subtotal: float = Field(ge=0)
    total: float = Field(ge=0)
    status: str
    created_at: str = Field(description="UTC ISO-8601 timestamp of when the order was created")
