import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.repositories import menu_repositories


def test_concurrent_additions_preserve_all_menu_items(tmp_path, monkeypatch):
    menus_file = tmp_path / "menus.json"
    menus_file.write_text(json.dumps([
        {"id": 1, "restaurant_id": 10, "items": [{"id": 3, "name": "Salad"}]},
        {"id": 1, "restaurant_id": 20, "items": [{"id": 9, "name": "Soup"}]},
    ]))
    monkeypatch.setattr(menu_repositories, "MENUS_FILE", menus_file)
    start = Barrier(4)

    def add_item(name):
        start.wait(timeout=5)
        return menu_repositories.add_item(10, 1, {"name": name})

    names = ["Rice", "Noodles", "Bread", "Fries"]
    with ThreadPoolExecutor(max_workers=len(names)) as executor:
        added = list(executor.map(add_item, names))

    menu = menu_repositories.get_menu(10, 1)
    assert menu["items"][0] == {"id": 3, "name": "Salad"}
    assert sorted(item["id"] for item in added) == [4, 5, 6, 7]
    assert {item["name"] for item in menu["items"][1:]} == set(names)
    assert menu_repositories.get_menu(20, 1)["items"] == [{"id": 9, "name": "Soup"}]
