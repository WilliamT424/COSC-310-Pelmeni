import pytest
from app.schemas.customer import Address, CustomerCreate
from app.services import customer_services
import json
from app.repositories import customer_repositories

@pytest.fixture
def sample_customer():
    return CustomerCreate(name="Test Customer", email="test@example.com", address=Address(street="123 Test Street", city="Kelowna", province="BC", postal_code="V1Y 1A1", country="Canada"), street="123 Test Street", city="Kelowna", province="BC", postal_code="V1Y 1A1", country="Canada")

@pytest.fixture
def mock_customer_repository(monkeypatch):
    customers = []

    def mock_read_all():
        return customers

    def mock_read(customer_id):
        return [c for c in customers if c["id"] == customer_id]

    def mock_write(customer_id, customer_data):
        if hasattr(customer_data, "model_dump"):
            customer_data = customer_data.model_dump()

        existing = next((c for c in customers if c["id"] == customer_id), None)

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
    customer = customer_services.retrieve_customer(registered.id)

    assert customer.id == registered.id
    assert customer.name == "Test Customer"
    assert customer.email == "test@example.com"


def test_retrieve_nonexistent_customer(mock_customer_repository):
    customer = customer_services.retrieve_customer(999)

    assert customer is None


def test_update_customer_information(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.id, {"name": "Updated Name", "email": "updated@example.com"})

    assert updated.name == "Updated Name"
    assert updated.email == "updated@example.com"


def test_update_delivery_address(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.id, {"street": "456 New Street", "city": "Vancouver"})

    assert updated.address.street == "456 New Street"
    assert updated.address.city == "Vancouver"
    assert updated.address.province == "BC"


def test_deactivate_customer(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    deactivated = customer_services.deactivate_customer(registered.id)

    assert deactivated.id == registered.id
    assert deactivated.status == False


def test_deactivate_nonexistent_customer(mock_customer_repository):
    customer = customer_services.deactivate_customer(999)

    assert customer is None

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

    updated = customer_services.update_customer(registered.id, {"name": "New Name"})

    assert updated.name == "New Name"
    assert updated.email == "test@example.com"
    assert updated.address.street == "123 Test Street"

def test_update_one_address_field(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    updated = customer_services.update_customer(registered.id, {"city": "Vancouver"})

    assert updated.address.city == "Vancouver"
    assert updated.address.street == "123 Test Street"
    assert updated.address.province == "BC"
    assert updated.address.postal_code == "V1Y 1A1"
    assert updated.address.country == "Canada"

def test_deactivation_is_saved(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)

    customer_services.deactivate_customer(registered.id)

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
            "postalCode": "V1Y 1A1",
            "country": "Canada"
        },
        "status": True
    }]
    file_path.write_text(json.dumps(customers))

    monkeypatch.setattr(customer_services, "read_all_customers_json_file", lambda: customer_repositories.read_all_customers_json_file(file_path))
    monkeypatch.setattr(customer_services, "read_customer_json_file", lambda customer_id: customer_repositories.read_customer_json_file(customer_id, file_path))
    monkeypatch.setattr(customer_services, "write_customer_json_file", lambda customer_id, data: customer_repositories.write_customer_json_file(customer_id, data, file_path))

    return file_path


def test_register_customer_integration(sample_customer, real_customer_repository):
    customer = customer_services.register_new_customer(sample_customer)
    saved = json.loads(real_customer_repository.read_text())
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
    assert duplicate.email == "test@example.com"
    assert len(mock_customer_repository) == 1

def test_update_nonexistent_customer(mock_customer_repository):
    result = customer_services.update_customer(999, {"name": "New Name"})
    assert result is None

def test_update_multiple_address_fields(sample_customer, mock_customer_repository):
    registered = customer_services.register_new_customer(sample_customer)
    updated = customer_services.update_customer(registered.id, {"street": "456 New Street", "city": "Vancouver", "province": "ON", "postal_code": "K1A 0B1", "country": "Canada"})
    assert updated.address.street == "456 New Street"
    assert updated.address.city == "Vancouver"
    assert updated.address.province == "ON"
    assert updated.address.postal_code == "K1A 0B1"
    assert updated.address.country == "Canada"