import pytest

from auth_support import (
    CUSTOMER, DEFAULT_ROLE, LOGIN_PATH, MANAGER, ME_PATH, PASSWORD, REGISTER_PATH,
    bearer, login, register, tamper, token_for,
)

pytestmark = pytest.mark.usefixtures("isolated_users")


# --- Registration ---------------------------------------------------------------------------

#Checks that a new user can register and is told their username and role
def test_register_returns_201_with_username_and_role(auth_client):
    response = register(auth_client, "alice", role=CUSTOMER)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == CUSTOMER

#Checks that a role is optional and falls back to the default role
def test_register_without_role_uses_default_role(auth_client):
    response = register(auth_client, "alice")
    assert response.status_code == 201
    assert response.json()["role"] == DEFAULT_ROLE

#Checks that the response never exposes the password or a hash of it
def test_register_response_does_not_leak_password(auth_client):
    body = register(auth_client, "alice").json()
    assert PASSWORD not in str(body)
    assert not any("password" in key.lower() or "hash" in key.lower() for key in body)

#Checks that a username cannot be registered twice
def test_register_duplicate_username_returns_409(auth_client):
    assert register(auth_client, "alice").status_code == 201
    assert register(auth_client, "alice").status_code == 409

#Checks that a duplicate registration cannot overwrite the original user's password
def test_duplicate_registration_does_not_replace_original_password(auth_client):
    register(auth_client, "alice", password=PASSWORD)
    register(auth_client, "alice", password="attacker-password")
    assert login(auth_client, "alice", PASSWORD).status_code == 200
    assert login(auth_client, "alice", "attacker-password").status_code == 401

#Checks that a role the system does not define is rejected
def test_register_unknown_role_returns_422(auth_client):
    assert register(auth_client, "alice", role="superuser").status_code == 422

#Checks that missing or empty credentials are rejected
@pytest.mark.parametrize("body", [
    {},
    {"username": "alice"},
    {"username": "alice", "password": ""},
])
def test_register_invalid_body_returns_422(auth_client, body):
    assert auth_client.post(REGISTER_PATH, json=body).status_code == 422


# --- Login ----------------------------------------------------------------------------------

#Checks that valid credentials return a bearer access token
def test_login_with_valid_credentials_returns_token(auth_client):
    register(auth_client, "alice")
    response = login(auth_client, "alice")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["token_type"].lower() == "bearer"

#Checks that a wrong password is rejected as unauthenticated
def test_login_wrong_password_returns_401(auth_client):
    register(auth_client, "alice")
    assert login(auth_client, "alice", "wrong-password").status_code == 401

#Checks that an unknown username is rejected the same way as a wrong password,
#so the API does not reveal whether a username exists
def test_login_failures_are_indistinguishable(auth_client):
    register(auth_client, "alice")
    wrong_password = login(auth_client, "alice", "wrong-password")
    unknown_user = login(auth_client, "nobody", "wrong-password")
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()

#Checks that missing credentials are a validation error, not a server error
@pytest.mark.parametrize("body", [{}, {"username": "alice"}])
def test_login_missing_fields_returns_422(auth_client, body):
    assert auth_client.post(LOGIN_PATH, json=body).status_code == 422


# --- Identifying the authenticated user ------------------------------------------------------

#Checks that the backend identifies the user (and role) behind a valid token
@pytest.mark.parametrize("role", [CUSTOMER, MANAGER])
def test_me_returns_authenticated_user(auth_client, role):
    token = token_for(auth_client, "alice", role)
    response = auth_client.get(ME_PATH, headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert response.json()["role"] == role

#Checks that each token identifies its own user, not whoever logged in last
def test_me_distinguishes_between_users(auth_client):
    alice = token_for(auth_client, "alice", CUSTOMER)
    bob = token_for(auth_client, "bob", MANAGER)
    assert auth_client.get(ME_PATH, headers=bearer(alice)).json()["username"] == "alice"
    assert auth_client.get(ME_PATH, headers=bearer(bob)).json()["username"] == "bob"

#Checks that a request with no credentials is unauthenticated and says how to authenticate
def test_me_without_token_returns_401(auth_client):
    response = auth_client.get(ME_PATH)
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers["www-authenticate"].lower().startswith("bearer")

#Checks that tokens which are malformed, forged or use the wrong scheme are rejected
@pytest.mark.parametrize("header", [
    "Bearer",
    "Bearer not-a-real-token",
    "Basic YWxpY2U6cGFzc3dvcmQ=",
    "",
])
def test_me_with_invalid_credentials_returns_401(auth_client, header):
    assert auth_client.get(ME_PATH, headers={"Authorization": header}).status_code == 401

#Checks that a valid token whose contents were altered is rejected
def test_me_with_tampered_token_returns_401(auth_client):
    token = token_for(auth_client, "alice", CUSTOMER)
    assert auth_client.get(ME_PATH, headers=bearer(tamper(token))).status_code == 401

#Checks that the user and role are not taken from client-controlled headers
def test_me_ignores_spoofed_identity_headers(auth_client):
    token = token_for(auth_client, "alice", CUSTOMER)
    spoofed = {**bearer(token), "X-User": "admin", "X-Username": "admin", "X-Role": MANAGER, "Role": MANAGER}
    body = auth_client.get(ME_PATH, headers=spoofed).json()
    assert body["username"] == "alice"
    assert body["role"] == CUSTOMER
