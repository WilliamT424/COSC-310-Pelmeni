from schemas.customer import Customer, Address, CustomerCreate, CustomerUpdate
from repositories.customer_repositories import read_all_customers_json_file, read_customer_json_file, write_customer_json_file


def create_customer(name: str, email: str, address: Address, status: bool) -> Customer:

    current_customers = read_all_customers_json_file()
    customer_id = max([customer.id for customer in current_customers], default=0) + 1

    return Customer(
        id=customer_id,
        name=name,
        email=email,
        address=address,
        status=status
    )

def create_address(street: str, city: str, province: str, postal_code: str, country: str) -> Address:   
    return Address(
        street=street,
        city=city,
        province=province,
        postal_code=postal_code,
        country=country
    )


def register_new_customer(customer: CustomerCreate):
    delivery_address = create_address(customer.address.street, customer.address.city, customer.address.province, customer.address.postal_code, customer.address.country)
    customer_data = create_customer(customer.name, customer.email, delivery_address, delivery_address, customer.status)
    
    write_customer_json_file(customer_data.id, customer_data)
    return customer_data


def retrieve_customer(customer_id: int):
    customer_data = read_customer_json_file(customer_id)
    if customer_data:
        return Customer(**customer_data[0])
    return None


def update_customer(customer_id: int, update_data: dict):

    customer_data = read_customer_json_file(customer_id)
    if not customer_data:
        return "Customer not found"

    customer_data = customer_data[0]

    for key, value in update_data.items():
        if key == "street" or key == "city" or key == "province" or key == "postal_code" or key == "country":
            customer_data["address"].update({key: value})
        else:
            customer_data[key] = value

    write_customer_json_file(customer_id, customer_data)
    
    return Customer(**customer_data)    

def deactivate_customer(customer_id: int):
    customer_data = read_customer_json_file(customer_id)
    if not customer_data:
        return "Customer not found"

    customer_data = customer_data[0]
    customer_data["status"] = False

    write_customer_json_file(customer_id, customer_data)
    
    return Customer(**customer_data)
