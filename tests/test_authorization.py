import json

import pytest

from auth_support import (
    CASEY_EMAIL, CASEY_ID, CUSTOMER_PATH, MANAGER, MORGAN_ID, NEW_RESTAURANT, PROTECTED_OPERATIONS,
    PUBLIC_AUTH_PATHS, PUBLIC_READ_PATHS, bearer, not_implemented, send, tamper, token_for,
)

pytestmark = pytest.mark.usefixtures("isolated_users")

operations = pytest.mark.parametrize(
    "method, path, body, ok_status",
    [op[1:] for op in PROTECTED_OPERATIONS],
    ids=[op[0] for op in PROTECTED_OPERATIONS],
)

OWN_ACCOUNT = CUSTOMER_PATH.format(customer_id=CASEY_ID)
OTHER_ACCOUNT = CUSTOMER_PATH.format(customer_id=MORGAN_ID)
MISSING_ACCOUNT = CUSTOMER_PATH.format(customer_id="CUST-0000")
ACCOUNT_REQUESTS = pytest.mark.parametrize("method, body", [("GET", None), ("PATCH", {"name": "Hijacked"})])

@ACCOUNT_REQUESTS
def test_account_without_token_returns_401(auth_client, method, body):
    response = send(auth_client, method, OTHER_ACCOUNT, body)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].lower().startswith("bearer")

@ACCOUNT_REQUESTS
def test_account_with_invalid_token_returns_401(auth_client, method, body):
    tampered = bearer(tamper(token_for(auth_client, CASEY_EMAIL)))
    assert send(auth_client, method, OWN_ACCOUNT, body, tampered).status_code == 401
    assert send(auth_client, method, OWN_ACCOUNT, body, bearer("not-a-real-token")).status_code == 401

@ACCOUNT_REQUESTS
def test_account_of_another_customer_returns_403(auth_client, customer_headers, method, body):
    response = send(auth_client, method, OTHER_ACCOUNT, body, customer_headers)
    assert response.status_code == 403
    assert "detail" in response.json()

@ACCOUNT_REQUESTS
def test_account_that_does_not_exist_returns_403_not_404(auth_client, customer_headers, method, body):
    assert send(auth_client, method, MISSING_ACCOUNT, body, customer_headers).status_code == 403

def test_account_of_another_customer_with_invalid_body_returns_403_not_422(auth_client, customer_headers):
    assert send(auth_client, "PATCH", OTHER_ACCOUNT, {"name": ""}, customer_headers).status_code == 403

def test_forbidden_account_update_does_not_modify_data(auth_client, customer_headers, isolated_users):
    before = isolated_users.read_text()
    send(auth_client, "PATCH", OTHER_ACCOUNT, {"name": "Hijacked"}, customer_headers)
    assert json.loads(isolated_users.read_text()) == json.loads(before)

def test_account_ignores_spoofed_identity_headers(auth_client, customer_headers):
    spoofed = {**customer_headers, "X-User": MORGAN_ID, "X-Customer-Id": MORGAN_ID}
    assert send(auth_client, "GET", OTHER_ACCOUNT, None, spoofed).status_code == 403

@operations
def test_manager_write_succeeds(auth_client, manager_headers, method, path, body, ok_status):
    assert send(auth_client, method, path, body, manager_headers).status_code == ok_status

def test_manager_invalid_body_returns_422(auth_client, manager_headers):
    assert send(auth_client, "POST", "/restaurants", {"name": "No Rating"}, manager_headers).status_code == 422

def test_manager_missing_resource_returns_404(auth_client, manager_headers):
    assert send(auth_client, "PATCH", "/restaurants/999", {"name": "x"}, manager_headers).status_code == 404

def test_manager_create_is_visible_to_everyone(auth_client, manager_headers):
    created = send(auth_client, "POST", "/restaurants", NEW_RESTAURANT, manager_headers).json()
    assert auth_client.get(f"/restaurants/{created['id']}").json()["name"] == NEW_RESTAURANT["name"]

def test_public_reads_work_without_token(auth_client):
    for path in PUBLIC_READ_PATHS:
        assert auth_client.get(path).status_code == 200, f"GET {path} should be public"

def test_public_reads_work_with_token(auth_client, customer_headers):
    assert auth_client.get("/restaurants", headers=customer_headers).status_code == 200

KNOWN_UNPROTECTED = {
    ("POST", "/restaurants"), ("PATCH", "/restaurants/{restaurant_id}"),
    ("POST", "/restaurants/{restaurant_id}/menus/{menu_id}/items"),
    ("PATCH", "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}"),
}

def _write_routes():
    from fastapi.routing import APIRoute
    from app.main import app
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path not in PUBLIC_AUTH_PATHS:
            for method in route.methods & {"POST", "PUT", "PATCH", "DELETE"}:
                yield method, route.path

def _write_route_params():
    for method, path in sorted(_write_routes()):
        marks = [not_implemented] if (method, path) in KNOWN_UNPROTECTED else []
        yield pytest.param(method, path, marks=marks, id=f"{method}-{path}")

@pytest.mark.parametrize("method, path", list(_write_route_params()))
def test_every_write_route_requires_authentication(auth_client, method, path):
    concrete_path = (path.replace("{restaurant_id}", "101").replace("{menu_id}", "1")
                     .replace("{item_id}", "1").replace("{customer_id}", CASEY_ID))
    assert send(auth_client, method, concrete_path, {}).status_code == 401, f"{method} {path} is not protected"

def test_write_route_discovery_finds_all_known_operations():
    assert KNOWN_UNPROTECTED | {("PATCH", "/customers/{customer_id}")} <= set(_write_routes())
