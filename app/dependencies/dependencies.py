from fastapi import Depends, HTTPException
from jwt import InvalidTokenError

from app.services.auth_services import decode_access_token
from app.repositories.customer_repositories import read_customer_json_file

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    try:
        token_data = decode_access_token(token)
        customer_id = token_data["sub"]

        if not isinstance(customer_id, str) or not customer_id:
            raise ValueError("Invalid customer ID")

    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    customers = read_customer_json_file(customer_id)

    if not customers:
        raise HTTPException(
            status_code=401,
            detail="Customer not found"
        )

    customer = customers[0]

    if customer["status"] != "active":
        raise HTTPException(
            status_code=401,
            detail="Account is inactive"
        )

    return customer


def require_customer_ownership(customer_id: str,customer=Depends(get_current_user)): #int or str? 
    if customer["customerId"] != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another customer's account"
        )

    return customer

