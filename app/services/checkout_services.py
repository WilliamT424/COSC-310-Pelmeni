from datetime import datetime, timezone

from app.repositories.cart_repository import get_cart
from app.repositories.order_repository import read_orders_file, write_orders_file
from app.schemas.order import Order
from app.services.cart_services import calculate_cart_totals, clear_cart
from app.services.customer_services import retrieve_customer
from app.services.menu_services import list_menu_items
from app.services.restaurant_services import get_restaurant

ORDER_STATUS_PENDING = "pending"


class CheckoutError(Exception):
    """Base class: checkout could not proceed and nothing was saved."""


class CustomerNotFound(CheckoutError):
    """The customer doesn't exist or is inactive."""


class CartNotFound(CheckoutError):
    pass


class InvalidCart(CheckoutError):
    """The cart breaks a business rule (empty, bad quantity, missing restaurant or item, unavailable item)."""


def _reprice_items(cart: dict) -> list[dict]:
    """Validate every cart line against current menu data and rebuild it with the current name and price.

    Prices stored in the cart are never trusted.
    """
    if not cart["items"]:
        raise InvalidCart("Cart is empty")

    items = []
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
        items.append({
            "menu_item_id": item["id"],
            "menu_id": line["menu_id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity,
        })
    return items


def checkout(customer_id: int, restaurant_id: int) -> dict:
    """Turn the customer's cart for a restaurant into a saved order.

    Order of operations matters: validate, reprice, save the order, and only then clear the cart.
    If anything fails before the order is saved the cart is left untouched.
    Raises a CheckoutError subclass when the checkout is refused.
    """
    customer = retrieve_customer(customer_id)
    if customer is None or not customer.status:
        raise CustomerNotFound(f"Customer {customer_id} not found or inactive")

    cart = get_cart(customer_id, restaurant_id)
    if cart is None:
        raise CartNotFound(f"Customer {customer_id} has no cart for restaurant {restaurant_id}")

    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise InvalidCart(f"Restaurant {restaurant_id} no longer exists")

    items = _reprice_items(cart)
    totals = calculate_cart_totals({"items": items})  # same calculation the cart uses, on current prices

    orders = read_orders_file()
    order = Order(
        orderId=max((o["orderId"] for o in orders), default=0) + 1,
        customerId=customer.customerId,
        restaurant_id=restaurant["id"],
        restaurant_name=restaurant["name"],
        deliveryAddress=customer.deliveryAddress,
        items=items,
        subtotal=totals["subtotal"],
        total=totals["total"],
        status=ORDER_STATUS_PENDING,
        created_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()
    orders.append(order)
    write_orders_file(orders)

    clear_cart(customer_id, restaurant_id)  # only after the order is safely persisted
    return order
