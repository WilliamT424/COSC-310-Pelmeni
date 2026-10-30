from pwdlib import PasswordHash
import jwt
import os
from app.repositories.customer_repositories import read_all_customers_json_file
from datetime import datetime, timedelta, timezone

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def get_customer_by_email (email: str):
    users = read_all_customers_json_file() 

    for user in users:  
        if user["email"] == email:
            return user 
    return None 

def authenticate_user(email: str, password: str):
    customer = get_customer_by_email(email)

    if customer is None:
        return None

    if customer.get("status") != "active":
        return None

    hashed_password = customer.get("hashed_password")

    if not hashed_password:
        return None

    if not verify_password(password, hashed_password):
        return None

    return customer


SECRET_KEY = os.environ["JWT_SECRET_KEY"]

def create_access_token(user_id: str) -> str: #fix later, user id = str or id

    expiration = datetime.now(timezone.utc) + timedelta(minutes=30)

    token_data = {
        "sub": user_id,
        "exp": expiration
    }

    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    return token


def decode_access_token(token: str):
    data = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]}
    )

    return data







