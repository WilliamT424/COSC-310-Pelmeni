def test_list_restaurants_returns_200(client):
    response = client.get("/restaurants")
    assert response.status_code == 200


def test_list_restaurants_returns_isolated_dataset(client, sample_restaurants):
    response = client.get("/restaurants")
    body = response.json()["restaurants"]

    assert len(body) == len(sample_restaurants)
    assert {r["id"] for r in body} == {r["id"] for r in sample_restaurants}


def test_list_restaurants_preserves_restaurant_fields(client, sample_restaurants):
    response = client.get("/restaurants")
    body = response.json()["restaurants"]

    target = sample_restaurants[0]
    match = next(r for r in body if r["id"] == target["id"])
    assert match["name"] == target["name"]
    assert match["cuisine"] == target["cuisine"]


def test_list_restaurants_rejects_unsupported_method(client):
    response = client.post("/restaurants")
    assert response.status_code == 405
