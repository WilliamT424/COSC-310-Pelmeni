from app.repositories.order_repository import get_order, get_orders_by_customer, read_orders_file, write_orders_file

ORDER_STATUS_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["ready"],
    "ready": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


class OrderNotFound(Exception):
    pass


class InvalidOrderTransition(Exception):
    pass

def retrieve_order(order_id: int):
    return get_order(order_id)


def retrieve_customer_orders(customer_id: int):
    return get_orders_by_customer(customer_id)


def update_order_status(order_id: int, new_status: str):
    orders = read_orders_file()

    order = next(
        (order for order in orders if order["orderId"] == order_id),
        None,
    )

    if order is None:
        raise OrderNotFound(f"Order {order_id} not found")

    current_status = order["status"]

    if new_status not in ORDER_STATUS_TRANSITIONS.get(current_status, []):
        raise InvalidOrderTransition(
            f"Cannot transition order from '{current_status}' to '{new_status}'"
        )

    order["status"] = new_status

    write_orders_file(orders)

    return order