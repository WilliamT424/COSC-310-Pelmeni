"""Shared constants and helpers for the authentication / authorization tests.

The auth tests are written before the implementation, so everything they assume about the API
contract lives in this one file. If the implementation differs (paths, field names, role names),
change it here and the tests follow.
"""

# --- Assumed API contract ----------------------------------------------------------------------
REGISTER_PATH = "/auth/register"   # POST {username, password, role?} -> 201 {username, role}
LOGIN_PATH = "/auth/login"         # POST {username, password}        -> 200 {access_token, token_type}
ME_PATH = "/auth/me"               # GET with bearer token            -> 200 {username, role}
PUBLIC_AUTH_PATHS = {REGISTER_PATH, LOGIN_PATH}   # the only write routes reachable without a token

CUSTOMER = "customer"
MANAGER = "manager"
DEFAULT_ROLE = CUSTOMER            # role given when registering without one

PASSWORD = "S3cure-pass!"

# Sample data comes from conftest.py: restaurants 101/102, menu 1 (restaurant 101) with items 1 and 2.
NEW_RESTAURANT = {"name": "Auth Cafe", "rating": 4.2, "cuisine": "Fusion", "deliveryTime": 20}
NEW_ITEM = {"name": "Soda", "description": "Cold", "price": 2.5, "available": True}

# Every operation that changes data: (id, method, path, valid body, status when permitted).
PROTECTED_OPERATIONS = [
    ("create-restaurant", "POST", "/restaurants", NEW_RESTAURANT, 201),
    ("update-restaurant", "PATCH", "/restaurants/101", {"name": "Renamed Bistro"}, 200),
    ("add-menu-item", "POST", "/restaurants/101/menus/1/items", NEW_ITEM, 201),
    ("update-menu-item", "PATCH", "/restaurants/101/menus/1/items/1", {"price": 12.5}, 200),
]

# Read-only endpoints that stay open to everyone (customers browse without an account).
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


# --- Helpers -------------------------------------------------------------------------------------
def register(client, username, password=PASSWORD, role=None):
    body = {"username": username, "password": password}
    if role is not None:
        body["role"] = role
    return client.post(REGISTER_PATH, json=body)


def login(client, username, password=PASSWORD):
    return client.post(LOGIN_PATH, json={"username": username, "password": password})


def token_for(client, username, role, password=PASSWORD):
    """Register a user and return a valid access token for them."""
    assert register(client, username, password, role).status_code == 201
    response = login(client, username, password)
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def send(client, method, path, body=None, headers=None):
    return client.request(method, path, json=body, headers=headers)


def tamper(token):
    """Flip the last character of a token so its signature no longer matches."""
    return token[:-1] + ("A" if token[-1] != "A" else "B")
