def test_list_restaurants_returns_200(client):
    response = client.get("/restaurants")
    assert response.status_code == 200


def test_list_restaurants_returns_isolated_dataset(client, sample_restaurants):
    response = client.get("/restaurants")
    body = response.json()

    assert len(body) == len(sample_restaurants)
    assert {r["id"] for r in body} == {r["id"] for r in sample_restaurants}


def test_get_single_restaurant_by_id(client, sample_restaurants):
    target = sample_restaurants[0]

    response = client.get(f"/restaurants/{target['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == target["name"]


def test_get_restaurant_with_unknown_id_returns_404(client):
    response = client.get("/restaurants/999999")
    assert response.status_code == 404
