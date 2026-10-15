from app.repositories.menu_repositories import read_menus_file


def list_menus_for_restaurant(restaurant_id: int) -> list[dict]:
    data = read_menus_file()
    menus = [
        menu
        for menu in data
        if menu["restaurant_id"] == restaurant_id
    ]
    return menus

