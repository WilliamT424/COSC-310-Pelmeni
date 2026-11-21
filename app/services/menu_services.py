from app.repositories import menu_repositories
from app.schemas.menu import MenuItemCreate, MenuItemUpdate


def list_menus_for_restaurant(restaurant_id: int) -> list[dict]:
    return menu_repositories.list_menus(restaurant_id)


def list_menu_items(restaurant_id: int, menu_id: int) -> list[dict] | None:
    """Items of one menu belonging to a restaurant, or None if that menu doesn't exist."""
    menu = menu_repositories.get_menu(restaurant_id, menu_id)
    return menu["items"] if menu is not None else None


def get_menu_item(restaurant_id: int, menu_id: int, item_id: int) -> dict | None:
    """A single item from a restaurant's menu, or None if the menu or item doesn't exist."""
    items = list_menu_items(restaurant_id, menu_id)
    if items is None:
        return None
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def add_menu_item(restaurant_id: int, menu_id: int, new_item: MenuItemCreate) -> dict | None:
    return menu_repositories.add_item(restaurant_id, menu_id, new_item.model_dump())


def update_menu_item(restaurant_id: int, menu_id: int, item_id: int, updates: MenuItemUpdate) -> dict | None:
    changes = updates.model_dump(exclude_unset=True)
    return menu_repositories.update_item(restaurant_id, menu_id, item_id, changes)
