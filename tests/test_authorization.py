import pytest

from auth_support import (
    CUSTOMER, MANAGER, NEW_RESTAURANT, PROTECTED_OPERATIONS, PUBLIC_AUTH_PATHS, PUBLIC_READ_PATHS,
    bearer, send, tamper, token_for,
)

pytestmark = pytest.mark.usefixtures("isolated_users")

operations = pytest.mark.parametrize(
    "method, path, body, ok_status",
    [op[1:] for op in PROTECTED_OPERATIONS],
    ids=[op[0] for op in PROTECTED_OPERATIONS],
)


# --- Unauthenticated requests -> 401 -----------------------------------------------------------

#Checks that every write operation rejects a request that carries no credentials
@operations
def test_write_without_token_returns_401(auth_client, method, path, body, ok_status):
    response = send(auth_client, method, path, body)
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers["www-authenticate"].lower().startswith("bearer")

#Checks that a write rejects a token that is invalid or uses the wrong scheme
@pytest.mark.parametrize("headers", [
    {"Authorization": "Bearer not-a-real-token"},
    {"Authorization": "Basic YWxpY2U6cGFzc3dvcmQ="},
    {"Authorization": "Bearer"},
])
def test_write_with_invalid_token_returns_401(auth_client, headers):
    assert send(auth_client, "POST", "/restaurants", NEW_RESTAURANT, headers).status_code == 401

#Checks that a valid token which has been altered no longer grants access
def test_write_with_tampered_token_returns_401(auth_client):
    token = token_for(auth_client, "morgan", MANAGER)
    response = send(auth_client, "PATCH", "/restaurants/101", {"name": "x"}, bearer(tamper(token)))
    assert response.status_code == 401

#Checks that anonymous callers cannot probe which restaurants exist
#(authentication is also decided before the body is validated; the route-scan test below covers that)
def test_anonymous_write_to_missing_resource_returns_401_not_404(auth_client):
    assert send(auth_client, "PATCH", "/restaurants/999", {"name": "x"}).status_code == 401


# --- Authenticated but not permitted -> 403 ------------------------------------------------------

#Checks that a customer is forbidden from every write operation
@operations
def test_customer_write_returns_403(auth_client, customer_headers, method, path, body, ok_status):
    response = send(auth_client, method, path, body, customer_headers)
    assert response.status_code == 403
    assert "detail" in response.json()

#Checks that the role check happens before body validation
def test_customer_invalid_body_returns_403_not_422(auth_client, customer_headers):
    assert send(auth_client, "POST", "/restaurants", {"rating": 99}, customer_headers).status_code == 403

#Checks that a customer cannot learn which resources exist from the error code
def test_customer_write_to_missing_resource_returns_403_not_404(auth_client, customer_headers):
    assert send(auth_client, "PATCH", "/restaurants/999", {"name": "x"}, customer_headers).status_code == 403


# --- Permitted users -----------------------------------------------------------------------------

#Checks that a manager can perform every write operation
@operations
def test_manager_write_succeeds(auth_client, manager_headers, method, path, body, ok_status):
    assert send(auth_client, method, path, body, manager_headers).status_code == ok_status

#Checks that a manager still gets the normal validation error for bad data
def test_manager_invalid_body_returns_422(auth_client, manager_headers):
    assert send(auth_client, "POST", "/restaurants", {"name": "No Rating"}, manager_headers).status_code == 422

#Checks that a manager still gets the normal 404 for a missing resource
def test_manager_missing_resource_returns_404(auth_client, manager_headers):
    assert send(auth_client, "PATCH", "/restaurants/999", {"name": "x"}, manager_headers).status_code == 404

#Checks that a manager's request really changes the data
def test_manager_create_is_visible_to_everyone(auth_client, manager_headers):
    created = send(auth_client, "POST", "/restaurants", NEW_RESTAURANT, manager_headers).json()
    assert auth_client.get(f"/restaurants/{created['id']}").json()["name"] == NEW_RESTAURANT["name"]


# --- Rejected requests must not change anything --------------------------------------------------

#Checks that anonymous and customer writes leave restaurants and menu items untouched
def test_rejected_writes_do_not_modify_data(auth_client, customer_headers):
    restaurants_before = auth_client.get("/restaurants").json()
    items_before = auth_client.get("/restaurants/101/menus/1/items").json()
    for _, method, path, body, _ in PROTECTED_OPERATIONS:
        send(auth_client, method, path, body)
        send(auth_client, method, path, body, customer_headers)
    assert auth_client.get("/restaurants").json() == restaurants_before
    assert auth_client.get("/restaurants/101/menus/1/items").json() == items_before


# --- Role comes from the server, never from the client ---------------------------------------------

#Checks that a role claim in a header, the body or the query string cannot elevate a customer
def test_customer_cannot_elevate_role_from_the_request(auth_client, customer_headers):
    headers = {**customer_headers, "X-Role": MANAGER, "Role": MANAGER, "X-User-Role": MANAGER}
    assert send(auth_client, "POST", "/restaurants", NEW_RESTAURANT, headers).status_code == 403
    body = {**NEW_RESTAURANT, "role": MANAGER}
    assert send(auth_client, "POST", "/restaurants?role=manager", body, customer_headers).status_code == 403


# --- Read endpoints stay public ----------------------------------------------------------------------

#Checks that customers can still browse without logging in
def test_public_reads_work_without_token(auth_client):
    for path in PUBLIC_READ_PATHS:
        assert auth_client.get(path).status_code == 200, f"GET {path} should be public"

#Checks that logged-in users can browse too
def test_public_reads_work_with_token(auth_client, customer_headers):
    assert auth_client.get("/restaurants", headers=customer_headers).status_code == 200


# --- Coverage guard: no write route can be added without protection --------------------------------------

def _write_routes():
    from fastapi.routing import APIRoute
    from app.main import app
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path not in PUBLIC_AUTH_PATHS:
            for method in route.methods & {"POST", "PUT", "PATCH", "DELETE"}:
                yield method, route.path

#Checks that every state-changing route (except register/login) refuses anonymous callers even with
#an empty (invalid) body, so a newly added write endpoint without a guard fails this test
@pytest.mark.parametrize("method, path", sorted(_write_routes()))
def test_every_write_route_requires_authentication(auth_client, method, path):
    concrete_path = path.replace("{restaurant_id}", "101").replace("{menu_id}", "1").replace("{item_id}", "1")
    assert send(auth_client, method, concrete_path, {}).status_code == 401, f"{method} {path} is not protected"

#Checks that the guard above actually found the write routes it is meant to protect
def test_write_route_discovery_finds_all_known_operations():
    assert {
        ("POST", "/restaurants"), ("PATCH", "/restaurants/{restaurant_id}"),
        ("POST", "/restaurants/{restaurant_id}/menus/{menu_id}/items"),
        ("PATCH", "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}"),
    } <= set(_write_routes())
