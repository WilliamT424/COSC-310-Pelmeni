from app.repositories.cart_repository import read_carts_file, write_carts_file, generate_cart_id
from app.services.menu_services import get_menu_item
from app.services.customer_services import retrieve_customer

def create_cart(customer_id: int, restaurant_id: int):
    customer = retrieve_customer(customer_id)

    if customer is None or not customer.status:
        return None

    carts = read_carts_file()

    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            return cart

    new_cart = {
        "id": generate_cart_id(),
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "items": []
    }
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
    customer = retrieve_customer(customer_id)

    if quantity <= 0:
        return None

    if customer is None or not customer.status:
        return None

    item = get_menu_item(restaurant_id, menu_id, item_id)

    if item is None or not item["available"]:
        return None

    carts = read_carts_file()
    cart = None

    for existing_cart in carts:
        if existing_cart["customer_id"] == customer_id and existing_cart["restaurant_id"] == restaurant_id:
            cart = existing_cart
            break

    if cart is None:
        cart = {
            "id": generate_cart_id(),
            "customer_id": customer_id,
            "restaurant_id": restaurant_id,
            "items": []
        }
        carts.append(cart)

    for cart_item in cart["items"]:
        if cart_item["menu_item_id"] == item_id and cart_item["menu_id"] == menu_id:
            cart_item["quantity"] += quantity
            write_carts_file(carts)
            return cart

    cart["items"].append({
        "menu_item_id": item_id,
        "menu_id": menu_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity
    })

    write_carts_file(carts)

    return cart

def update_cart_item(customer_id: int, restaurant_id: int, menu_id: int, item_id: int, quantity: int):
    customer = retrieve_customer(customer_id)

    if quantity <= 0:
        return None

    if customer is None or not customer.status:
        return None

    
    carts = read_carts_file()

    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            for cart_item in cart["items"]:
                if cart_item["menu_item_id"] == item_id and cart_item["menu_id"] == menu_id:
                    cart_item["quantity"] = quantity
                    write_carts_file(carts)
                    return cart

    return None

def remove_cart_item(customer_id: int, restaurant_id: int, menu_id: int, item_id: int):
    customer = retrieve_customer(customer_id)

    if customer is None or not customer.status:
        return None

    carts = read_carts_file()

    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            for cart_item in cart["items"]:
                if cart_item["menu_item_id"] == item_id and cart_item["menu_id"] == menu_id:
                    cart["items"].remove(cart_item)
                    write_carts_file(carts)
                    return cart

    return None

def clear_cart(customer_id: int, restaurant_id: int):
    customer = retrieve_customer(customer_id)

    if customer is None or not customer.status:
        return None

    carts = read_carts_file()

    for cart in carts:
        if cart["customer_id"] == customer_id and cart["restaurant_id"] == restaurant_id:
            cart["items"] = []
            write_carts_file(carts)
            return cart

    return None

def calculate_cart_totals(cart):
    subtotal = sum(
        item["price"] * item["quantity"]
        for item in cart["items"]
    )

    return {
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2)
    }

