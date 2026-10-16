from app.repositories.menu_repositories import read_menus_file


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
