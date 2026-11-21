import pytest
from schemas.customer import Address, CustomerCreate, Customer
from services import customer_services
import json
from repositories import customer_repositories

@pytest.fixture
def sample_customer():
    return CustomerCreate(name="Test Customer", email="test@example.com", street="123 Test Street", city="Kelowna", province="BC", postal_code="V1Y 1A1", country="Canada")

@pytest.fixture
def mock_customer_repository(monkeypatch):
    customers = []

    def mock_read_all():
        return customers

    def mock_read(customer_id):
        return [c for c in customers if c["customerId"] == customer_id]

    def mock_write(customer_id, customer_data):
        if hasattr(customer_data, "model_dump"):
            customer_data = customer_data.model_dump()

        existing = next((c for c in customers if c["customerId"] == customer_id), None)

        if existing:
            existing.update(customer_data)
        else:
            customers.append(customer_data)

        return True

    monkeypatch.setattr(customer_services, "read_all_customers_json_file", mock_read_all)
    monkeypatch.setattr(customer_services, "read_customer_json_file", mock_read)
    monkeypatch.setattr(customer_services, "write_customer_json_file", mock_write)

    return customers

def test_register_customer(sample_customer, mock_customer_repository):
    customer = customer_services.register_new_customer(sample_customer)

    assert customer.name == "Test Customer"
    assert customer.email == "test@example.com"
    assert customer.status == True
    assert len(mock_customer_repository) == 1


def test_retrieve_customer(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)
    customer = customer_services.retrieve_customer(registered.customerId) 

    assert customer.customerId == registered.customerId
    assert customer.name == "Test Customer"
    assert customer.email == "test@example.com"


def test_retrieve_nonexistent_customer(mock_customer_repository):
    customer = customer_services.retrieve_customer(999)

    assert customer is None


def test_update_customer_information(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.customerId, {"name": "Updated Name", "email": "updated@example.com"})

    assert updated.name == "Updated Name"
    assert updated.email == "updated@example.com"


def test_update_delivery_address(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.customerId, {"street": "456 New Street", "city": "Vancouver"})

    assert updated.deliveryAddress.street == "456 New Street"
    assert updated.deliveryAddress.city == "Vancouver"
    assert updated.deliveryAddress.province == "BC"


def test_deactivate_customer(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    deactivated = customer_services.deactivate_customer(registered.customerId)

    assert deactivated.customerId == registered.customerId
    assert deactivated.status == False


def test_deactivate_nonexistent_customer(mock_customer_repository):
    customer = customer_services.deactivate_customer(999)

    assert customer == None

def test_read_all_customers(tmp_path):
    file_path = tmp_path / "customers.json"
    customers = [{"customerId": 1, "name": "John"}, {"customerId": 2, "name": "Jane"}]
    file_path.write_text(json.dumps(customers))

    result = customer_repositories.read_all_customers_json_file(file_path)

    assert len(result) == 2
    assert result[0]["name"] == "John"
    assert result[1]["name"] == "Jane"

def test_read_customer_by_id(tmp_path):
    file_path = tmp_path / "customers.json"
    customers = [{"customerId": 1, "name": "John"}, {"customerId": 2, "name": "Jane"}]
    file_path.write_text(json.dumps(customers))

    result = customer_repositories.read_customer_json_file(2, file_path)

    assert len(result) == 1
    assert result[0]["name"] == "Jane"

def test_write_new_customer_preserves_existing(tmp_path):
    file_path = tmp_path / "customers.json"
    customers = [{"customerId": 1, "name": "John"}]
    file_path.write_text(json.dumps(customers))

    new_customer = {"customerId": 2, "name": "Jane"}
    customer_repositories.write_customer_json_file(2, new_customer, file_path)

    result = json.loads(file_path.read_text())

    assert len(result) == 2
    assert result[0]["name"] == "John"
    assert result[1]["name"] == "Jane"

def test_update_existing_customer(tmp_path):
    file_path = tmp_path / "customers.json"
    customers = [{"customerId": 1, "name": "John", "email": "john@example.com"}]
    file_path.write_text(json.dumps(customers))

    updated_customer = {"customerId": 1, "name": "Updated John", "email": "new@example.com"}
    customer_repositories.write_customer_json_file(1, updated_customer, file_path)

    result = json.loads(file_path.read_text())

    assert len(result) == 1
    assert result[0]["name"] == "Updated John"
    assert result[0]["email"] == "new@example.com"

def test_update_name_preserves_other_information(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.customerId, {"name": "New Name"})

    assert updated.name == "New Name"
    assert updated.email == "test@example.com"
    assert updated.deliveryAddress.street == "123 Test Street"

def test_update_one_address_field(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.customerId, {"city": "Vancouver"})

    assert updated.deliveryAddress.city == "Vancouver"
    assert updated.deliveryAddress.street == "123 Test Street"
    assert updated.deliveryAddress.province == "BC"
    assert updated.deliveryAddress.postal_code == "V1Y 1A1"
    assert updated.deliveryAddress.country == "Canada"

def test_deactivation_is_saved(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    customer_services.deactivate_customer(registered.customerId)

    assert mock_customer_repository[0]["status"] == False

@pytest.fixture
def real_customer_repository(tmp_path, monkeypatch):
    file_path = tmp_path / "customers.json"
    customers = [{
        "customerId": 1,
        "name": "John",
        "email": "john@example.com",
        "deliveryAddress": {
            "street": "123 Test Street",
            "city": "Kelowna",
            "province": "BC",
            "postal_code": "V1Y 1A1",
            "country": "Canada"
        },
        "status": True
    }]
    file_path.write_text(json.dumps(customers))

    def write_customer(customer_id, customer_data):
        if hasattr(customer_data, "model_dump"):
            customer_data = customer_data.model_dump()

        return customer_repositories.write_customer_json_file(
            customer_id,
            customer_data,
            file_path
        )

    monkeypatch.setattr(
        customer_services,
        "write_customer_json_file",
        write_customer
    )

    monkeypatch.setattr(customer_services, "read_all_customers_json_file", lambda: customer_repositories.read_all_customers_json_file(file_path))
    monkeypatch.setattr(customer_services, "read_customer_json_file", lambda customer_id: customer_repositories.read_customer_json_file(customer_id, file_path))
    return file_path


def test_register_customer_integration(sample_customer, real_customer_repository):
    customer = customer_services.register_new_customer(sample_customer)
    saved = json.loads(real_customer_repository.read_text())
    assert isinstance(customer, Customer)
    assert customer.name == "Test Customer"
    assert len(saved) == 2


def test_retrieve_customer_integration(real_customer_repository):
    customer = customer_services.retrieve_customer(1)
    assert customer.name == "John"
    assert customer.email == "john@example.com"


def test_update_customer_integration(real_customer_repository):
    customer = customer_services.update_customer(1, {"name": "Updated John"})
    saved = json.loads(real_customer_repository.read_text())
    assert customer.name == "Updated John"
    assert saved[0]["name"] == "Updated John"


def test_deactivate_customer_integration(real_customer_repository):
    customer = customer_services.deactivate_customer(1)
    saved = json.loads(real_customer_repository.read_text())
    assert customer.status is False
    assert saved[0]["status"] is False


def test_register_duplicate_email(sample_customer, mock_customer_repository):
    customer_services.register_new_customer(sample_customer)
    duplicate = customer_services.register_new_customer(sample_customer)
    
    assert len(mock_customer_repository) == 1
    assert duplicate == "Please update your existing account instead of creating a new one."

def test_update_nonexistent_customer(mock_customer_repository):
    result = customer_services.update_customer(999, {"name": "New Name"})
    assert result == None

def test_update_multiple_address_fields(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)
    updated = customer_services.update_customer(registered.customerId, {"street": "456 New Street", "city": "Vancouver", "province": "ON", "postal_code": "K1A 0B1", "country": "Canada"})
    assert updated.deliveryAddress.street == "456 New Street"
    assert updated.deliveryAddress.city == "Vancouver"
    assert updated.deliveryAddress.province == "ON"
    assert updated.deliveryAddress.postal_code == "K1A 0B1"
    assert updated.deliveryAddress.country == "Canada"