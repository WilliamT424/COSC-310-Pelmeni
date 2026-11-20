import functools

import pytest

from app.services.passwords import hash_password

LOGIN_PATH = "/auth/login"
ME_PATH = "/auth/me"
CUSTOMER_PATH = "/customers/{customer_id}"
CUSTOMERS_PATH = "/customers"

REGISTER_PATH = "/auth/register"
PUBLIC_AUTH_PATHS = {REGISTER_PATH, LOGIN_PATH, CUSTOMERS_PATH}
CUSTOMER = "customer"
MANAGER = "manager"
DEFAULT_ROLE = CUSTOMER

PASSWORD = "S3cure-pass!"

not_implemented = pytest.mark.xfail(
    reason="planned feature, not implemented in the backend yet", strict=True,
)

#customerId is an int in the stored data; the JWT "sub" claim is its string form (str(customerId))
CASEY_ID, CASEY_EMAIL = 9001, "casey.customer@example.com"
MORGAN_ID, MORGAN_EMAIL = 9002, "morgan.manager@example.com"
INACTIVE_ID, INACTIVE_EMAIL = 9003, "ian.inactive@example.com"
NO_PASSWORD_ID, NO_PASSWORD_EMAIL = 9004, "nora.nopassword@example.com"
MISSING_ID = 999999

@functools.cache
def _hashed_password():
    return hash_password(PASSWORD)

def _customer(customer_id, name, email, active=True, with_password=True):
    #Same shape as data/customers.json (the backend has no role field yet)
    customer = {
        "customerId": customer_id,
        "name": name,
        "email": email,
        "deliveryAddress": {
            "street": "1 Test Street", "city": "Kelowna", "province": "BC",
            "postal_code": "V1V 1V1", "country": "Canada",
        },
        "status": active,
    }
    if with_password:
        customer["hashed_password"] = _hashed_password()
    return customer

def sample_customers():
    return [
        _customer(CASEY_ID, "Casey Customer", CASEY_EMAIL),
        _customer(MORGAN_ID, "Morgan Manager", MORGAN_EMAIL),
        _customer(INACTIVE_ID, "Ian Inactive", INACTIVE_EMAIL, active=False),
        _customer(NO_PASSWORD_ID, "Nora NoPassword", NO_PASSWORD_EMAIL, with_password=False),
    ]

NEW_RESTAURANT = {"name": "Auth Cafe", "rating": 4.2, "cuisine": "Fusion", "deliveryTime": 20}
NEW_ITEM = {"name": "Soda", "description": "Cold", "price": 2.5, "available": True}

PROTECTED_OPERATIONS = [
    ("create-restaurant", "POST", "/restaurants", NEW_RESTAURANT, 201),
    ("update-restaurant", "PATCH", "/restaurants/101", {"name": "Renamed Bistro"}, 200),
    ("add-menu-item", "POST", "/restaurants/101/menus/1/items", NEW_ITEM, 201),
    ("update-menu-item", "PATCH", "/restaurants/101/menus/1/items/1", {"price": 12.5}, 200),
]

PUBLIC_READ_PATHS = [
    "/",
    "/health",
    "/restaurants",
    "/restaurants/search?cuisine=test",
    "/restaurants/101",
    "/restaurants/101/menus",
    "/restaurants/101/menus/1/items",
    "/restaurants/101/menus/1/items/1",
]

def register(client, email, password=PASSWORD, role=None):
    body = {"email": email, "password": password}
    if role is not None:
        body["role"] = role
    return client.post(REGISTER_PATH, json=body)

def login(client, email, password=PASSWORD):
    return client.post(LOGIN_PATH, json={"email": email, "password": password})

def token_for(client, email, password=PASSWORD):
    response = login(client, email, password)
    assert response.status_code == 200
    return response.json()["access_token"]

def bearer(token):
    return {"Authorization": f"Bearer {token}"}

def send(client, method, path, body=None, headers=None):
    return client.request(method, path, json=body, headers=headers)

def tamper(token):
    header, payload, signature = token.split(".")
    return ".".join([header, payload, ("A" if signature[0] != "A" else "B") + signature[1:]])
