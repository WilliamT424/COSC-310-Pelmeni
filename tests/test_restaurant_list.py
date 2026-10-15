#Checks that the restaurant-list endpoint responds successfully
def test_list_restaurants_returns_200(client):
    response = client.get("/restaurants")
    assert response.status_code == 200


#Confirms that the endpoint uses the isolated test data rather than accidentally returning the real dataset
def test_list_restaurants_returns_isolated_dataset(client, sample_restaurants):  
    response = client.get("/restaurants")
    body = response.json()["restaurants"]

    assert len(body) == len(sample_restaurants)
    assert {r["id"] for r in body} == {r["id"] for r in sample_restaurants}

#Verifies that important restaurant fields are returned correctly, and not just that the number of restaurants is correct
def test_list_restaurants_preserves_restaurant_fields(client, sample_restaurants):
    response = client.get("/restaurants")
    body = response.json()["restaurants"]

    target = sample_restaurants[0]
    match = next(r for r in body if r["id"] == target["id"])
    assert match["name"] == target["name"]
    assert match["cuisine"] == target["cuisine"]


#Verifies that clients cannot use an unsupported HTTP method on this endpoint
def test_list_restaurants_rejects_unsupported_method(client):
    response = client.post("/restaurants")
    assert response.status_code == 405


#Verifies that the restaurant details endpoint works for an existing restaurant
def test_get_restaurant_returns_200(client):
    response = client.get("/restaurants/101")
    assert response.status_code == 200

#Verifies the correctness of the returned restaurant details.
def test_get_restaurant_returns_correct_data(client):
    response = client.get("/restaurants/101")
    assert response.json()["name"] == "Test Bistro"
    assert response.json()["cuisine"] == "Test"

#Verifies that your endpoint handles a nonexistent restaurant properly --> not returning a successful response
def test_get_missing_restaurant_returns_404(client):
    response = client.get("/restaurants/999")
    assert response.status_code == 404

#Verifies that unsupported HTTP methods are rejected
def test_get_restaurant_rejects_unsupported_method(client):
    response = client.post("/restaurants/101")
    assert response.status_code == 405
