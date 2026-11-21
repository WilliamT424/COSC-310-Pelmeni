import pytest


def test_frontend_index_is_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "Pelmeni" in response.text


def test_frontend_script_is_served(client):
    response = client.get("/ui/app.js")
    assert response.status_code == 200
    assert "/restaurants/search" in response.text


def test_api_routes_still_work_with_frontend_mounted(client):
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/restaurants").status_code == 200


def test_frontend_script_uses_menu_item_edit_endpoints(client):
    script = client.get("/ui/app.js").text
    assert 'jsonRequest("POST"' in script
    assert 'jsonRequest("PATCH"' in script


def test_frontend_script_does_not_choose_restaurant_ids(client):
    assert "data.id" not in client.get("/ui/app.js").text


# Checkout workflow: the sequence of API calls the frontend makes ----------------

@pytest.fixture
def workflow(auth_client, tmp_path, monkeypatch):
    import app.repositories.cart_repository as cart_repository
    import app.repositories.order_repository as order_repository
    carts_file, orders_file = tmp_path / "carts.json", tmp_path / "orders.json"
    carts_file.write_text("[]")
    orders_file.write_text("[]")
    monkeypatch.setattr(cart_repository, "CARTS_FILE", carts_file)
    # The order repository takes its file as a default argument, so patch the defaults
    for name in ("read_orders_file", "write_orders_file", "get_order", "get_orders_by_customer"):
        function = getattr(order_repository, name)
        monkeypatch.setattr(function, "__defaults__", (orders_file,))
    return auth_client


def test_customer_workflow_the_frontend_drives(workflow):
    """Same sequence of calls the UI makes: register, sign in, build a cart, check out, view the order."""
    registration = {"name": "Fran Frontend", "email": "fran@example.com", "password": "longenough1",
                    "street": "1 Main St", "city": "Kelowna", "province": "BC",
                    "postal_code": "V1V 1V1", "country": "Canada"}
    assert workflow.post("/customers", json=registration).status_code == 201

    token = workflow.post("/auth/login", json={"email": registration["email"], "password": registration["password"]}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = workflow.get("/auth/me", headers=headers).json()
    cart_path = f"/customers/{me['customerId']}/cart"

    add = lambda quantity: workflow.post(f"{cart_path}/items", headers=headers, json={
        "restaurant_id": 101, "menu_id": 1, "menu_item_id": 1, "quantity": quantity})
    assert add(1).status_code == 200
    query = {"restaurant_id": 101, "menu_id": 1}
    assert workflow.patch(f"{cart_path}/items/1", headers=headers, params=query, json={"quantity": 3}).status_code == 200

    cart = workflow.get(cart_path, headers=headers, params={"restaurant_id": 101}).json()
    assert cart["total"] == 29.97  # 3 x 9.99, calculated by the backend

    order = workflow.post(f"/customers/{me['customerId']}/checkout", headers=headers, params={"restaurant_id": 101})
    assert order.status_code == 201
    order = order.json()
    assert order["total"] == 29.97 and order["status"] == "pending"

    assert workflow.get(f"/orders/{order['orderId']}", headers=headers).json() == order
    assert workflow.get(cart_path, headers=headers, params={"restaurant_id": 101}).json()["items"] == []
    assert workflow.get(f"/customers/{me['customerId']}/orders", headers=headers).json()["orders"] == [order]


def test_cart_and_checkout_reject_other_customers(workflow, customer_headers):
    other = "/customers/9002"
    assert workflow.get(f"{other}/cart", headers=customer_headers, params={"restaurant_id": 101}).status_code == 403
    assert workflow.post(f"{other}/checkout", headers=customer_headers, params={"restaurant_id": 101}).status_code == 403
    assert workflow.get(f"{other}/orders", headers=customer_headers).status_code == 403


def test_checkout_of_empty_cart_is_refused_and_creates_no_order(workflow, customer_headers):
    path = "/customers/9001"
    workflow.get(f"{path}/cart", headers=customer_headers, params={"restaurant_id": 101})
    response = workflow.post(f"{path}/checkout", headers=customer_headers, params={"restaurant_id": 101})
    assert response.status_code == 409
    assert workflow.get(f"{path}/orders", headers=customer_headers).json() == {"orders": []}


def test_every_cart_change_returns_backend_totals(workflow, customer_headers):
    """The cart page re-renders straight from these responses, so each one needs subtotal and total."""
    cart_path = "/customers/9001/cart"
    item = {"restaurant_id": 101, "menu_id": 1, "menu_item_id": 1, "quantity": 1}
    query = {"restaurant_id": 101, "menu_id": 1}

    responses = [
        workflow.post(f"{cart_path}/items", headers=customer_headers, json=item),                      # new line
        workflow.post(f"{cart_path}/items", headers=customer_headers, json=item),                      # existing line
        workflow.patch(f"{cart_path}/items/1", headers=customer_headers, params=query, json={"quantity": 4}),
        workflow.delete(f"{cart_path}/items/1", headers=customer_headers, params=query),
        workflow.delete(cart_path, headers=customer_headers, params={"restaurant_id": 101}),
    ]
    assert [r.status_code for r in responses] == [200] * 5
    assert [r.json()["total"] for r in responses] == [9.99, 19.98, 39.96, 0, 0]
    assert all(r.json()["subtotal"] == r.json()["total"] for r in responses)
