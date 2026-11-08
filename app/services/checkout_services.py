from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.repositories.cart_repositories import close_cart, get_active_cart
from app.repositories.order_repositories import read_orders_file, write_orders_file
from app.schemas.order import Order, OrderItem
from app.services.customer_stub import customer_exists
from app.services.menu_services import list_menu_items
from app.services.restaurant_services import get_restaurant

ORDER_STATUS_PENDING = "pending"


class CheckoutError(Exception):
    """Base class: checkout could not proceed and nothing was saved."""


class CustomerNotFound(CheckoutError):
    pass


class ActiveCartNotFound(CheckoutError):
    pass


class InvalidCart(CheckoutError):
    """The cart breaks a business rule (empty, bad quantity, missing restaurant or item, unavailable item)."""


def _cents(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _price_cart(cart: dict) -> tuple[dict, list[OrderItem]]:
    """Validate the cart against current restaurant and menu data and price every line from it.

    Returns (restaurant, order items). Prices in the cart are never trusted.
    """
    restaurant = get_restaurant(cart["restaurant_id"])
    if restaurant is None:
        raise InvalidCart(f"Restaurant {cart['restaurant_id']} no longer exists")
    if not cart["items"]:
        raise InvalidCart("Cart is empty")

    order_items = []
    for line in cart["items"]:
        quantity = line["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise InvalidCart(f"Invalid quantity for menu item {line['menu_item_id']}")
        menu_items = list_menu_items(cart["restaurant_id"], line["menu_id"])
        item = next((i for i in menu_items or [] if i["id"] == line["menu_item_id"]), None)
        if item is None:
            raise InvalidCart(f"Menu item {line['menu_item_id']} not found on this restaurant's menu")
        if not item["available"]:
            raise InvalidCart(f"Menu item '{item['name']}' is not available")
        unit_price = _cents(item["price"])
        order_items.append(OrderItem(
            menu_id=line["menu_id"],
            menu_item_id=item["id"],
            name=item["name"],
            unit_price=float(unit_price),
            quantity=quantity,
            line_total=float(unit_price * quantity),
        ))
    return restaurant, order_items


def checkout(customer_id: int) -> dict:
    """Turn the customer's active cart into a saved order.

    Order of operations matters: validate, price, save the order, and only then close the cart.
    If anything fails before the order is saved the cart is left untouched.
    Raises a CheckoutError subclass when the checkout is refused.
    """
    if not customer_exists(customer_id):
        raise CustomerNotFound(f"Customer {customer_id} not found")
    cart = get_active_cart(customer_id)
    if cart is None:
        raise ActiveCartNotFound(f"Customer {customer_id} has no active cart")

    restaurant, order_items = _price_cart(cart)
    subtotal = sum((_cents(i.line_total) for i in order_items), Decimal("0.00"))
    total = subtotal  # no taxes, fees or discounts are defined yet; this is the single place to add them

    orders = read_orders_file()
    order = Order(
        id=max((o["id"] for o in orders), default=0) + 1,
        customer_id=customer_id,
        restaurant_id=restaurant["id"],
        restaurant_name=restaurant["name"],
        items=order_items,
        subtotal=float(subtotal),
        total=float(total),
        status=ORDER_STATUS_PENDING,
        created_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()
    orders.append(order)
    write_orders_file(orders)

    close_cart(cart["id"])  # only after the order is safely persisted
    return order
