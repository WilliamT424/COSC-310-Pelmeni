from app.repositories.order_repositories import read_orders_file


def get_order(order_id: int) -> dict | None:
    """One order, or None if it doesn't exist."""
    for order in read_orders_file():
        if order["id"] == order_id:
            return order
    return None


def list_orders_for_customer(customer_id: int) -> list[dict]:
    """Every order placed by a customer, oldest first ([] if they have none)."""
    return [order for order in read_orders_file() if order["customer_id"] == customer_id]
