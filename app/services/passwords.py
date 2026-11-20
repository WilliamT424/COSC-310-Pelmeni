from pwdlib import PasswordHash
from app.repositories.customer_repositories import read_all_customers_json_file

password_hash = PasswordHash.recommended()
def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)