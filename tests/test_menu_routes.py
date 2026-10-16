#Checks that requesting the menus for an existing restaurant succeeds
def test_get_restaurant_menus_returns_200(client):
    response = client.get("/restaurants/101/menus")
    assert response.status_code == 200

#Checks that the endpoint returns the expected menu and its two items
def test_get_restaurant_menus_returns_correct_menu(client):
    response = client.get("/restaurants/101/menus")
    menu = response.json()[0]
    assert menu["name"] == "Test Bistro Menu"
    assert len(menu["items"]) == 2

#Checks that menu items include the correct availability values
def test_get_restaurant_menus_includes_availability(client):
    response = client.get("/restaurants/101/menus")
    items = response.json()[0]["items"]
    assert items[0]["available"] is True
    assert items[1]["available"] is False


#Checks that a request for a restaurant that does not exist returns 404
def test_get_missing_restaurant_menus_returns_404(client):
    response = client.get("/restaurants/999/menus")
    assert response.status_code == 404

#Checks that an existing restaurant with no menus returns an empty list rather than 404
def test_get_menus_for_restaurant_without_menus_returns_empty_list(client):
    response = client.get("/restaurants/102/menus")
    assert response.status_code == 200
    assert response.json() == []

#Checks that the endpoint rejects an unsupported HTTP method
def test_get_restaurant_menus_rejects_unsupported_method(client):
    response = client.post("/restaurants/101/menus")
    assert response.status_code == 405