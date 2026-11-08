from datetime import datetime, timedelta, timezone

import jwt
import pytest

from auth_support import (
    CASEY_EMAIL, CASEY_ID, CUSTOMER, DEFAULT_ROLE, INACTIVE_EMAIL, LOGIN_PATH, MANAGER, MORGAN_EMAIL,
    MORGAN_ID, ME_PATH, NO_PASSWORD_EMAIL, PASSWORD, REGISTER_PATH, bearer, login, not_implemented,
    register, tamper, token_for,
)

pytestmark = pytest.mark.usefixtures("isolated_users")

def make_token(secret=None, **claims):
    from app.services.auth_services import SECRET_KEY
    payload = {"sub": CASEY_ID, "exp": datetime.now(timezone.utc) + timedelta(minutes=5), **claims}
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(payload, secret or SECRET_KEY, algorithm="HS256")

def test_login_with_valid_credentials_returns_token(auth_client):
    response = login(auth_client, CASEY_EMAIL)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["token_type"].lower() == "bearer"

def test_login_token_identifies_customer_and_expires(auth_client):
    from app.services.auth_services import decode_access_token
    claims = decode_access_token(token_for(auth_client, CASEY_EMAIL))
    assert claims["sub"] == CASEY_ID
    assert datetime.fromtimestamp(claims["exp"], timezone.utc) > datetime.now(timezone.utc)

def test_login_response_does_not_leak_password(auth_client):
    body = login(auth_client, CASEY_EMAIL).json()
    assert PASSWORD not in str(body)
    assert not any("password" in key.lower() or "hash" in key.lower() for key in body)

def test_login_wrong_password_returns_401(auth_client):
    assert login(auth_client, CASEY_EMAIL, "wrong-password").status_code == 401

def test_login_failures_are_indistinguishable(auth_client):
    wrong_password = login(auth_client, CASEY_EMAIL, "wrong-password")
    unknown_email = login(auth_client, "nobody@example.com", "wrong-password")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()

def test_login_inactive_account_returns_401(auth_client):
    assert login(auth_client, INACTIVE_EMAIL).status_code == 401

@pytest.mark.parametrize("password", [PASSWORD, ""])
def test_login_account_without_password_returns_401(auth_client, password):
    assert login(auth_client, NO_PASSWORD_EMAIL, password).status_code == 401

@pytest.mark.parametrize("body", [{}, {"email": CASEY_EMAIL}, {"password": PASSWORD}])
def test_login_missing_fields_returns_422(auth_client, body):
    assert auth_client.post(LOGIN_PATH, json=body).status_code == 422

@pytest.mark.parametrize("email, customer_id, name", [
    (CASEY_EMAIL, CASEY_ID, "Casey Customer"),
    (MORGAN_EMAIL, MORGAN_ID, "Morgan Manager"),
])

def test_me_returns_authenticated_customer(auth_client, email, customer_id, name):
    response = auth_client.get(ME_PATH, headers=bearer(token_for(auth_client, email)))
    assert response.status_code == 200
    assert response.json() == {"customerId": customer_id, "name": name, "email": email}

def test_me_distinguishes_between_customers(auth_client):
    casey = token_for(auth_client, CASEY_EMAIL)
    morgan = token_for(auth_client, MORGAN_EMAIL)
    assert auth_client.get(ME_PATH, headers=bearer(casey)).json()["customerId"] == CASEY_ID
    assert auth_client.get(ME_PATH, headers=bearer(morgan)).json()["customerId"] == MORGAN_ID

def test_me_does_not_leak_password_hash(auth_client):
    body = auth_client.get(ME_PATH, headers=bearer(token_for(auth_client, CASEY_EMAIL))).json()
    assert not any("password" in key.lower() or "hash" in key.lower() for key in body)

def test_me_without_token_returns_401(auth_client):
    response = auth_client.get(ME_PATH)
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers["www-authenticate"].lower().startswith("bearer")

@pytest.mark.parametrize("header", [
    "Bearer",
    "Bearer not-a-real-token",
    "Basic YWxpY2U6cGFzc3dvcmQ=",
    "",
])
def test_me_with_invalid_credentials_returns_401(auth_client, header):
    assert auth_client.get(ME_PATH, headers={"Authorization": header}).status_code == 401

def test_me_with_tampered_token_returns_401(auth_client):
    token = token_for(auth_client, CASEY_EMAIL)
    assert auth_client.get(ME_PATH, headers=bearer(tamper(token))).status_code == 401

def test_me_with_token_signed_by_someone_else_returns_401(auth_client):
    forged = make_token(secret="not-the-real-secret-but-long-enough-for-hs256")
    assert auth_client.get(ME_PATH, headers=bearer(forged)).status_code == 401

def test_me_with_expired_token_returns_401(auth_client):
    expired = make_token(exp=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert auth_client.get(ME_PATH, headers=bearer(expired)).status_code == 401

@pytest.mark.parametrize("claims", [{"exp": None}, {"sub": None}])
def test_me_with_incomplete_token_returns_401(auth_client, claims):
    assert auth_client.get(ME_PATH, headers=bearer(make_token(**claims))).status_code == 401

def test_me_with_token_for_unknown_customer_returns_401(auth_client):
    unknown = make_token(sub="CUST-0000")
    assert auth_client.get(ME_PATH, headers=bearer(unknown)).status_code == 401

def test_me_with_token_of_deactivated_account_returns_401(auth_client, isolated_users):
    import json
    token = token_for(auth_client, CASEY_EMAIL)
    customers = json.loads(isolated_users.read_text())
    next(c for c in customers if c["customerId"] == CASEY_ID)["status"] = "inactive"
    isolated_users.write_text(json.dumps(customers))
    assert auth_client.get(ME_PATH, headers=bearer(token)).status_code == 401

def test_me_ignores_spoofed_identity_headers(auth_client):
    token = token_for(auth_client, CASEY_EMAIL)
    spoofed = {**bearer(token), "X-User": MORGAN_ID, "X-Customer-Id": MORGAN_ID, "X-Role": MANAGER, "Role": MANAGER}
    body = auth_client.get(ME_PATH, headers=spoofed).json()
    assert body["customerId"] == CASEY_ID
    assert body["email"] == CASEY_EMAIL