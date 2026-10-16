import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.repositories.menu_repositories as menu_repositories
import app.repositories.restaurant_repositories as restaurant_repositories
from app.main import app
from app.schemas.menu import menu as MenuModel
from app.schemas.restaurant import Restaurant

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOT = DATA_DIR.parent


@pytest.fixture
def files(tmp_path, monkeypatch):
    #Temp copies of the real dataset; the repositories are pointed at them
    restaurants = tmp_path / "restaurants.json"
    menus = tmp_path / "menus.json"
    shutil.copy(DATA_DIR / "restaurants.json", restaurants)
    shutil.copy(DATA_DIR / "menus.json", menus)
    monkeypatch.setattr(restaurant_repositories, "RESTAURANTS_FILE", restaurants)
    monkeypatch.setattr(menu_repositories, "MENUS_FILE", menus)
    return restaurants, menus


def load(path):
    return json.loads(path.read_text())


def new_client():
    #A fresh client per call: nothing is cached between requests, every read hits the file
    return TestClient(app)


NEW_RESTAURANT = {"id": 100, "name": "Persist Cafe", "rating": 4, "cuisine": "Test", "deliveryTime": 25}


# --- committed dataset is valid -----------------------------------------------

def test_committed_restaurants_are_valid_and_ids_unique():
    data = load(DATA_DIR / "restaurants.json")
    restaurants = [Restaurant(**r) for r in data]
    assert len({r.id for r in restaurants}) == len(restaurants)


def test_committed_menus_are_valid_and_consistent():
    restaurant_ids = {r["id"] for r in load(DATA_DIR / "restaurants.json")}
    menus = [MenuModel(**m) for m in load(DATA_DIR / "menus.json")]
    assert len({m.id for m in menus}) == len(menus)
    for m in menus:
        assert m.restaurant_id in restaurant_ids
        assert len({i.id for i in m.items}) == len(m.items)


# --- restaurants ---------------------------------------------------------------

def test_created_restaurant_is_written_to_file(files):
    restaurants, _ = files
    assert new_client().post("/restaurants", json=NEW_RESTAURANT).status_code == 201
    assert NEW_RESTAURANT in load(restaurants)


def test_created_restaurant_is_visible_to_a_new_client(files):
    new_client().post("/restaurants", json=NEW_RESTAURANT)
    body = new_client().get("/restaurants/100").json()
    assert body == NEW_RESTAURANT
    assert 100 in {r["id"] for r in new_client().get("/restaurants").json()["restaurants"]}


def test_created_restaurant_is_found_by_search(files):
    new_client().post("/restaurants", json=NEW_RESTAURANT)
    found = new_client().get("/restaurants/search?name=persist").json()["restaurants"]
    assert [r["id"] for r in found] == [100]


def test_restaurant_data_survives_a_process_restart(files):
    restaurants, _ = files
    new_client().post("/restaurants", json=NEW_RESTAURANT)
    code = (
        "import json, sys\n"
        "from app.repositories.restaurant_repositories import read_json_file\n"
        "print(json.dumps(read_json_file(sys.argv[1])))"
    )
    out = subprocess.run([sys.executable, "-c", code, str(restaurants)], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    assert NEW_RESTAURANT in json.loads(out)


def test_update_restaurant_is_written_and_leaves_others_untouched(files):
    restaurants, _ = files
    before = {r["id"]: r for r in load(restaurants)}
    assert new_client().patch("/restaurants/1", json={"name": "Renamed", "deliveryTime": 99}).status_code == 200
    after = {r["id"]: r for r in load(restaurants)}
    assert after[1]["name"] == "Renamed" and after[1]["deliveryTime"] == 99
    assert after[1]["cuisine"] == before[1]["cuisine"]
    assert {k: v for k, v in after.items() if k != 1} == {k: v for k, v in before.items() if k != 1}


def test_ids_stay_stable_and_unique_after_create_and_update(files):
    restaurants, _ = files
    before_ids = [r["id"] for r in load(restaurants)]
    new_client().post("/restaurants", json=NEW_RESTAURANT)
    new_client().patch("/restaurants/2", json={"name": "Renamed"})
    new_client().patch("/restaurants/3", json={"id": 777})  # id is not an updatable field
    after_ids = [r["id"] for r in load(restaurants)]
    assert after_ids == before_ids + [100]
    assert len(set(after_ids)) == len(after_ids)


def test_stored_restaurants_remain_valid_after_writes(files):
    restaurants, _ = files
    new_client().post("/restaurants", json=NEW_RESTAURANT)
    new_client().patch("/restaurants/1", json={"rating": 4})
    for r in load(restaurants):
        Restaurant(**r)
    assert new_client().get("/restaurants").status_code == 200


def test_duplicate_create_does_not_change_file(files):
    restaurants, _ = files
    before = restaurants.read_text()
    assert new_client().post("/restaurants", json={**NEW_RESTAURANT, "id": 1}).status_code == 409
    assert restaurants.read_text() == before


def test_invalid_create_does_not_change_file(files):
    restaurants, _ = files
    before = restaurants.read_text()
    assert new_client().post("/restaurants", json={"id": 100, "name": "Bad"}).status_code == 422
    assert restaurants.read_text() == before


def test_update_of_unknown_restaurant_does_not_change_file(files):
    restaurants, _ = files
    before = restaurants.read_text()
    assert new_client().patch("/restaurants/999", json={"name": "Ghost"}).status_code == 404
    assert restaurants.read_text() == before


# --- menus and the restaurant relationship -------------------------------------

def test_added_menu_item_is_written_and_readable_by_new_client(files):
    _, menus = files
    body = {"name": "Persist Dish", "description": "d", "price": 5.5, "available": True}
    created = new_client().post("/restaurants/1/menus/1/items", json=body).json()
    stored = next(m for m in load(menus) if m["id"] == 1)["items"]
    assert created in stored
    assert new_client().get(f"/restaurants/1/menus/1/items/{created['id']}").json() == created


def test_updated_menu_item_is_written_and_other_items_untouched(files):
    _, menus = files
    before = next(m for m in load(menus) if m["id"] == 1)["items"]
    new_client().patch("/restaurants/1/menus/1/items/1", json={"price": 1.23, "available": False})
    after = next(m for m in load(menus) if m["id"] == 1)["items"]
    assert after[0]["price"] == 1.23 and after[0]["available"] is False
    assert after[0]["name"] == before[0]["name"]
    assert after[1:] == before[1:]


def test_menu_item_ids_unique_and_relationships_consistent_after_writes(files):
    restaurants, menus = files
    for n in range(3):
        new_client().post("/restaurants/1/menus/1/items", json={"name": f"Dish {n}", "price": 1})
    restaurant_ids = {r["id"] for r in load(restaurants)}
    for m in load(menus):
        MenuModel(**m)
        assert m["restaurant_id"] in restaurant_ids
        assert len({i["id"] for i in m["items"]}) == len(m["items"])


def test_menu_item_edits_do_not_touch_restaurant_file(files):
    restaurants, _ = files
    before = restaurants.read_text()
    new_client().post("/restaurants/1/menus/1/items", json={"name": "X", "price": 1})
    assert restaurants.read_text() == before


def test_failed_menu_writes_do_not_change_file(files):
    _, menus = files
    before = menus.read_text()
    assert new_client().post("/restaurants/1/menus/99/items", json={"name": "X", "price": 1}).status_code == 404
    assert new_client().post("/restaurants/1/menus/1/items", json={"name": "X", "price": -1}).status_code == 422
    assert new_client().patch("/restaurants/1/menus/1/items/999", json={"price": 1}).status_code == 404
    assert menus.read_text() == before


def test_decimal_rating_update_is_stored_and_does_not_break_listing(files):
    restaurants, _ = files
    response = new_client().patch("/restaurants/1", json={"rating": 4.5})
    assert response.status_code == 200
    assert next(r for r in load(restaurants) if r["id"] == 1)["rating"] == 4.5
    assert new_client().get("/restaurants").status_code == 200
    assert new_client().get("/restaurants/1").json()["rating"] == 4.5
