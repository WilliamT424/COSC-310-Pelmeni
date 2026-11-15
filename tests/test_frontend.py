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
