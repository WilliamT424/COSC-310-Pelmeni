import pytest

import app.services.restaurant_services as restaurant_services
from app.services.restaurant_services import search_restaurants

DATA = [
    {"id": 1, "name": "Zakura", "rating": 5, "cuisine": "Japanese", "deliveryTime": 20},
    {"id": 2, "name": "Jasmine", "rating": 4, "cuisine": "Japanese", "deliveryTime": 45},
    {"id": 3, "name": "BurgerBay", "rating": 3, "cuisine": "American", "deliveryTime": 20},
]


@pytest.fixture
def search_client(client, monkeypatch):
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: [dict(r) for r in DATA])
    return client


def ids(response):
    return {r["id"] for r in response.json()["restaurants"]}


def test_search_no_filters_returns_all(search_client):
    assert ids(search_client.get("/restaurants/search")) == {1, 2, 3}


def test_search_by_name_is_case_insensitive_substring(search_client):
    assert ids(search_client.get("/restaurants/search?name=BURG")) == {3}


def test_search_by_cuisine(search_client):
    assert ids(search_client.get("/restaurants/search?cuisine=japanese")) == {1, 2}


def test_search_by_min_rating(search_client):
    assert ids(search_client.get("/restaurants/search?min_rating=4")) == {1, 2}


def test_search_by_decimal_min_rating(search_client):
    assert ids(search_client.get("/restaurants/search?min_rating=4.5")) == {1}


def test_search_by_max_delivery_time(search_client):
    assert ids(search_client.get("/restaurants/search?max_delivery_time=20")) == {1, 3}


def test_search_combines_filters(search_client):
    r = search_client.get("/restaurants/search?cuisine=japanese&max_delivery_time=30")
    assert ids(r) == {1}


def test_search_no_match_returns_empty_list(search_client):
    r = search_client.get("/restaurants/search?name=nothing")
    assert r.status_code == 200
    assert r.json() == {"restaurants": []}


@pytest.mark.parametrize("query", ["min_rating=abc", "min_rating=9", "min_rating=-1", "max_delivery_time=-5"])
def test_search_invalid_filter_returns_422(search_client, query):
    assert search_client.get(f"/restaurants/search?{query}").status_code == 422


def test_search_route_not_shadowed_by_restaurant_id_route(search_client):
    assert search_client.get("/restaurants/search").status_code != 422


def test_service_search_restaurants_filters(monkeypatch):
    monkeypatch.setattr(restaurant_services, "read_json_file", lambda: [dict(r) for r in DATA])
    assert [r["id"] for r in search_restaurants(cuisine="american")] == [3]
