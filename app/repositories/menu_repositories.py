import json
from pathlib import Path
from threading import RLock

from app.repositories.json_storage import atomic_write_json

current_dir = Path(__file__).resolve().parent.parent.parent
MENUS_FILE = current_dir / "data" / "menus.json"
# The item operations also hold this lock across the full read and write.
_menu_file_lock = RLock()


def read_menus_file(file_path=None):
    # Resolved at call time so tests can point MENUS_FILE at a temp copy
    with _menu_file_lock, open(file_path or MENUS_FILE, "r") as file:
        return json.load(file)


def write_menus_file(data, file_path=None):
    with _menu_file_lock:
        atomic_write_json(data, file_path or MENUS_FILE, indent=2)


def list_menus(restaurant_id: int) -> list[dict]:
    return [menu for menu in read_menus_file() if menu["restaurant_id"] == restaurant_id]


def _find_menu(menus: list[dict], restaurant_id: int, menu_id: int) -> dict | None:
    for menu in menus:
        if menu["restaurant_id"] == restaurant_id and menu["id"] == menu_id:
            return menu
    return None


def get_menu(restaurant_id: int, menu_id: int) -> dict | None:
    return _find_menu(read_menus_file(), restaurant_id, menu_id)


def add_item(restaurant_id: int, menu_id: int, item_data: dict) -> dict | None:
    with _menu_file_lock:
        menus = read_menus_file()
        menu = _find_menu(menus, restaurant_id, menu_id)
        if menu is None:
            return None
        items = menu["items"]
        next_id = max((item["id"] for item in items), default=0) + 1
        item = {**item_data, "id": next_id}
        items.append(item)
        write_menus_file(menus)
        return item


def update_item(restaurant_id: int, menu_id: int, item_id: int, changes: dict) -> dict | None:
    with _menu_file_lock:
        menus = read_menus_file()
        menu = _find_menu(menus, restaurant_id, menu_id)
        if menu is None:
            return None
        for item in menu["items"]:
            if item["id"] == item_id:
                item.update(changes)
                write_menus_file(menus)
                return item
    return None
