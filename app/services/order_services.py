from app.repositories.order_repository import get_order, get_orders_by_customer


def retrieve_order(order_id: int):
    return get_order(order_id)


def retrieve_customer_orders(customer_id: int):
    return get_orders_by_customer(customer_id)