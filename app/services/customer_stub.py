"""TEMPORARY customer check. Customer accounts are not merged into main yet.

Replace the body of customer_exists with a lookup in the real customer service once it lands.
"""


def customer_exists(customer_id: int) -> bool:
    return customer_id > 0
