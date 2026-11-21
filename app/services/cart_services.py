from app.repositories.cart_repository import read_carts_file, write_carts_file, generate_cart_id
from app.services.menu_services import get_menu_item
from app.services.customer_services import retrieve_customer


def _is_active_customer(customer_id: int) -> bool:
    customer = retrieve_customer(customer_id)
    return customer is not None and bool(customer.status)


def _find_cart(carts: list[dict], customer_id: int, restaurant_id: int | None) -> dict | None:
    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            return cart
    return None


def _find_cart_item(cart: dict, menu_id: int, item_id: int) -> dict | None:
    for cart_item in cart["items"]:
        if cart_item["menu_item_id"] == item_id and cart_item["menu_id"] == menu_id:
            return cart_item
    return None


def _new_cart(customer_id: int, restaurant_id: int | None) -> dict:
    return {
        "id": generate_cart_id(),
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "items": []
    }


def create_cart(customer_id: int, restaurant_id: int | None = None):
    if not _is_active_customer(customer_id):
        return None

    carts = read_carts_file()

    cart = _find_cart(carts, customer_id, restaurant_id)
    if cart is not None:
        return cart

    new_cart = _new_cart(customer_id, restaurant_id)
    carts.append(new_cart)
    write_carts_file(carts)
    return new_cart

def get_customer_cart(customer_id: int, restaurant_id: int):
    cart = create_cart(customer_id, restaurant_id)

    if cart is None:
        return None

    totals = calculate_cart_totals(cart)

    return {
        **cart,
        **totals
    }

def add_item_to_cart(customer_id: int, restaurant_id: int, menu_id: int, item_id: int, quantity: int):
    if quantity <= 0 or not _is_active_customer(customer_id):
        return None

    item = get_menu_item(restaurant_id, menu_id, item_id)

    if item is None or not item["available"]:
        return None

    carts = read_carts_file()
    cart = _find_cart(carts, customer_id, restaurant_id)

    if cart is None:
        cart = _new_cart(customer_id, restaurant_id)
        carts.append(cart)

    cart_item = _find_cart_item(cart, menu_id, item_id)
    if cart_item is not None:
        cart_item["quantity"] += quantity
        write_carts_file(carts)
        return _with_totals(cart)

    cart["items"].append({
        "menu_item_id": item_id,
        "menu_id": menu_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity
    })

    write_carts_file(carts)

    return _with_totals(cart)

def update_cart_item(customer_id: int, restaurant_id: int, menu_id: int, item_id: int, quantity: int):
    if quantity <= 0 or not _is_active_customer(customer_id):
        return None

    carts = read_carts_file()
    cart = _find_cart(carts, customer_id, restaurant_id)
    if cart is None:
        return None

    cart_item = _find_cart_item(cart, menu_id, item_id)
    if cart_item is None:
        return None

    cart_item["quantity"] = quantity
    write_carts_file(carts)
    return _with_totals(cart)

def remove_cart_item(customer_id: int, restaurant_id: int, menu_id: int, item_id: int):
    if not _is_active_customer(customer_id):
        return None

    carts = read_carts_file()
    cart = _find_cart(carts, customer_id, restaurant_id)
    if cart is None:
        return None

    cart_item = _find_cart_item(cart, menu_id, item_id)
    if cart_item is None:
        return None

    cart["items"].remove(cart_item)
    write_carts_file(carts)
    return _with_totals(cart)

def clear_cart(customer_id: int, restaurant_id: int):
    if not _is_active_customer(customer_id):
        return None

    carts = read_carts_file()
    cart = _find_cart(carts, customer_id, restaurant_id)
    if cart is None:
        return None

    cart["items"] = []
    write_carts_file(carts)
    return _with_totals(cart)

def _with_totals(cart: dict) -> dict:
    """The cart as returned to clients: every cart response carries the backend-calculated totals."""
    return {**cart, **calculate_cart_totals(cart)}

def calculate_cart_totals(cart):
    subtotal = sum(
        item["price"] * item["quantity"]
        for item in cart["items"]
    )

    return {
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2)
    }
