from pwdlib import PasswordHash
from app.schemas.customer import Customer, CustomerAuth
from repositories.customer_repositories import read_all_customers_json_file, read_customer_json_file, write_customer_json_file 

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def get_customer_by_email (email: str):
    users = read_all_customers_json_file() #check the method user.email, user["email"]

    for user in users:  
        if user["email"] == email:
            return user 
    return None 

def authenticate_user(email: str, password: str):
    customer = get_customer_by_email(email)

    if customer is None:
        return None

    if not verify_password(password, customer["hashed_password"]):
        return None

    if not customer["status"]:
        return None

    return customer








