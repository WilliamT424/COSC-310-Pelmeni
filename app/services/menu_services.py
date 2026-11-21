from app.repositories.menu_repositories import read_menus_file, write_menus_file
from app.schemas.menu import menuItem, MenuItemCreate, MenuItemUpdate


def list_menus_for_restaurant(restaurant_id: int) -> list[dict]:
    data = read_menus_file()
    menus = [
        menu
        for menu in data
        if menu["restaurant_id"] == restaurant_id
    ]
    return menus


def list_menu_items(restaurant_id: int, menu_id: int) -> list[dict] | None:
    """Items of one menu belonging to a restaurant, or None if that menu doesn't exist."""
    for menu in list_menus_for_restaurant(restaurant_id):
        if menu["id"] == menu_id:
            return menu["items"]
    return None


def get_menu_item(restaurant_id: int, menu_id: int, item_id: int) -> dict | None:
    """A single item from a restaurant's menu, or None if the menu or item doesn't exist."""
    items = list_menu_items(restaurant_id, menu_id)
    if items is None:
        return None
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def _find_menu(menus: list[dict], restaurant_id: int, menu_id: int) -> dict | None:
    for menu in menus:
        if menu["restaurant_id"] == restaurant_id and menu["id"] == menu_id:
            return menu
    return None


def add_menu_item(restaurant_id: int, menu_id: int, new_item: MenuItemCreate) -> dict | None:
    """Append an item to a menu with the next free item id. Returns None if the menu doesn't exist."""
    menus = read_menus_file()
    menu = _find_menu(menus, restaurant_id, menu_id)
    if menu is None:
        return None
    next_id = max((item["id"] for item in menu["items"]), default=0) + 1
    item = menuItem(id=next_id, **new_item.model_dump()).model_dump()
    menu["items"].append(item)
    write_menus_file(menus)
    return item


def update_menu_item(restaurant_id: int, menu_id: int, item_id: int, updates: MenuItemUpdate) -> dict | None:
    """Apply the provided fields to an item. Returns None if the menu or item doesn't exist."""
    menus = read_menus_file()
    menu = _find_menu(menus, restaurant_id, menu_id)
    if menu is None:
        return None
    for item in menu["items"]:
        if item["id"] == item_id:
            item.update(updates.model_dump(exclude_unset=True))
            write_menus_file(menus)
            return item
    return None
