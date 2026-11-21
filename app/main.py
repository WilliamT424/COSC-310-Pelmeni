from typing import Optional
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, status, HTTPException, Query
from app.services.order_services import retrieve_order, retrieve_customer_orders
from app.services.restaurant_services import create_restaurant_service, list_restaurants, get_restaurant, search_restaurants, update_restaurant_service
from app.services.menu_services import list_menus_for_restaurant, list_menu_items, get_menu_item, add_menu_item, update_menu_item
from app.services.checkout_services import checkout, CheckoutError, CustomerNotFound, CartNotFound
from app.schemas.menu import menuItem, MenuItemCreate, MenuItemUpdate
from app.schemas.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate
from app.services.customer_services import deactivate_customer, register_new_customer, retrieve_customer, update_customer
from app.services.auth_services import authenticate_user, create_access_token
from app.dependencies.dependencies import get_current_user, require_customer_ownership
from app.schemas.auth import LoginRequest, Token
from app.schemas.cart import Cart, CartItemCreate, CartItemUpdate
from app.schemas.order import Order, OrdersResponse
from app.services.cart_services import create_cart, get_customer_cart, add_item_to_cart, update_cart_item, remove_cart_item, clear_cart
from fastapi import Depends

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to Pelmeni!"}

@app.get("/health")
async def health(status_code: int = status.HTTP_200_OK):
    return {"status": "healthy"}

@app.get("/restaurants")
async def get_restaurants():
    data = list_restaurants()
    return {"restaurants": data}

@app.get(
    "/restaurants/search",
    summary="Search and filter restaurants",
    description="Returns restaurants matching all provided filters. With no filters, returns every restaurant. "
                "An empty result is returned as an empty list with status 200.",
    responses={422: {"description": "Invalid filter value (e.g. non-numeric or negative)"}},
)
async def search_restaurants_route(
    name: Optional[str] = Query(None, description="Case-insensitive substring of the restaurant name"),
    cuisine: Optional[str] = Query(None, description="Case-insensitive substring of the cuisine"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating (0-5)"),
    max_delivery_time: Optional[int] = Query(None, ge=0, description="Maximum delivery time in minutes"),
):
    return {"restaurants": search_restaurants(name, cuisine, min_rating, max_delivery_time)}

@app.get("/restaurants/{restaurant_id}") #get request to retrieve the details of a specific restaurant; 
async def restaurant_details(restaurant_id: int):
    restaurant = get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found by id")
    return restaurant

@app.get("/restaurants/{restaurant_id}/menus")  #get request to view menus
async def get_restaurant_menus(restaurant_id: int):
    if get_restaurant(restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return list_menus_for_restaurant(restaurant_id)

@app.get(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items",
    response_model=list[menuItem],
    summary="List menu items",
    description="Returns every item on the given menu of the given restaurant.",
    responses={404: {"description": "Menu not found for this restaurant"}},
)
async def get_menu_items(restaurant_id: int, menu_id: int):
    items = list_menu_items(restaurant_id, menu_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return items

@app.get(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}",
    response_model=menuItem,
    summary="Get a menu item",
    description="Returns a single item from the given menu of the given restaurant.",
    responses={404: {"description": "Menu or menu item not found"}},
)
async def get_single_menu_item(restaurant_id: int, menu_id: int, item_id: int):
    item = get_menu_item(restaurant_id, menu_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@app.get(
    "/customers/{customer_id}",
    response_model=Customer,
    summary="Get a customer",
    description="Returns a single customer by their ID.",
    responses={404: {"description": "Customer not found"}},
)
async def get_customer(customer_id: int, customer=Depends(require_customer_ownership)):
    customer = retrieve_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post(
    "/customers",
    status_code=201,
    response_model=Customer,
    summary="Create a customer",
    description="Creates a customer and persists it. The id is assigned by the server.",
    responses={422: {"description": "Invalid customer data"}},
)
async def create_customer(new_customer: CustomerCreate):
    return register_new_customer(new_customer)

@app.patch(
    "/customers/{customer_id}",
    response_model=Customer,
    summary="Update a customer",
    description="Updates only the provided fields of an existing customer.",
    responses={404: {"description": "Customer not found"}, 422: {"description": "Invalid customer data"}},
)
async def update_customer_route(customer_id: int, updates: CustomerUpdate,customer=Depends(require_customer_ownership)):
    customer = update_customer(customer_id, updates.model_dump(exclude_unset=True))
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.patch(
    "/customers/{customer_id}/deactivate",
    response_model=Customer,
    summary="Deactivate a customer",
    description="Deactivates an existing customer.",
    responses={404: {"description": "Customer not found"}, 422: {"description": "Invalid customer data"}},
)
async def deactivate_customer_route(customer_id: int ,customer=Depends(require_customer_ownership)):
    customer = deactivate_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post(
    "/customers/{customer_id}/cart",
    response_model=Cart,
    status_code=201,
    summary="Create or retrieve a customer's cart",
    description="Creates an empty cart for the customer and restaurant, or returns the existing cart.",
    responses={404: {"description": "Customer not found or inactive"}},
)
async def create_customer_cart(
    customer_id: int,
    restaurant_id: int | None = None,
    customer=Depends(require_customer_ownership)
):
    cart = create_cart(customer_id, restaurant_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Customer not found or inactive")
    return cart

@app.get(
    "/customers/{customer_id}/cart",
    response_model=Cart,
    summary="Retrieve a customer's cart",
    description="Returns the customer's cart for the specified restaurant, including calculated totals.",
    responses={404: {"description": "Customer not found or inactive"}},
)
async def get_customer_cart_route(
    customer_id: int,
    restaurant_id: int,
    customer=Depends(require_customer_ownership)
):
    cart = get_customer_cart(customer_id, restaurant_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Customer not found or inactive")
    return cart

@app.post(
    "/customers/{customer_id}/cart/items",
    response_model=Cart,
    summary="Add an item to a customer's cart",
    description="Adds an available menu item to the customer's cart. The item price is taken from the menu.",
    responses={404: {"description": "Customer or available menu item not found"}, 422: {"description": "Invalid quantity or item data"}},
)
async def add_item_to_customer_cart(
    customer_id: int,
    item: CartItemCreate,
    customer=Depends(require_customer_ownership)
):
    cart = add_item_to_cart(
        customer_id,
        item.restaurant_id,
        item.menu_id,
        item.menu_item_id,
        item.quantity
    )
    if cart is None:
        raise HTTPException(status_code=404, detail="Customer or available menu item not found")
    return cart

@app.patch(
    "/customers/{customer_id}/cart/items/{menu_item_id}",
    response_model=Cart,
    summary="Update cart item quantity",
    description="Updates the quantity of an item in the customer's cart.",
    responses={404: {"description": "Cart or item not found"}, 422: {"description": "Invalid quantity"}},
)
async def update_customer_cart_item(
    customer_id: int,
    menu_item_id: int,
    restaurant_id: int,
    menu_id: int,
    updates: CartItemUpdate,
    customer=Depends(require_customer_ownership)
):
    cart = update_cart_item(customer_id, restaurant_id, menu_id, menu_item_id, updates.quantity)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart

@app.delete(
    "/customers/{customer_id}/cart/items/{menu_item_id}",
    response_model=Cart,
    summary="Remove an item from a customer's cart",
    description="Removes the specified menu item from the customer's cart.",
    responses={404: {"description": "Cart or item not found"}},
)
async def remove_customer_cart_item(
    customer_id: int,
    menu_item_id: int,
    restaurant_id: int,
    menu_id: int,
    customer=Depends(require_customer_ownership)
):
    cart = remove_cart_item(customer_id, restaurant_id, menu_id, menu_item_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart

@app.delete(
    "/customers/{customer_id}/cart",
    response_model=Cart,
    summary="Clear a customer's cart",
    description="Removes all items from the customer's cart while keeping the cart.",
    responses={404: {"description": "Cart not found or customer inactive"}},
)
async def clear_customer_cart(
    customer_id: int,
    restaurant_id: int,
    customer=Depends(require_customer_ownership)
):
    cart = clear_cart(customer_id, restaurant_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found or customer inactive")
    return cart



@app.post(
    "/restaurants",
    status_code=201,
    response_model=Restaurant,
    summary="Create a restaurant",
    description="Creates a restaurant and persists it. The id is assigned by the server.",
    responses={422: {"description": "Invalid restaurant data (missing field, rating outside 0-5, negative delivery time, empty name or cuisine)"}},
)
async def create_restaurant(new_restaurant: RestaurantCreate):#roles needed, discuss with Gurnoor
   return create_restaurant_service(new_restaurant)

@app.patch(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    summary="Update a restaurant",
    description="Updates only the provided fields of an existing restaurant. The id cannot be changed and provided fields cannot be null.",
    responses={404: {"description": "Restaurant not found"}, 422: {"description": "Invalid restaurant data"}},
)
def update_restaurant_route( restaurant_id: int, updates: RestaurantUpdate):
    restaurant = update_restaurant_service(restaurant_id, updates.model_dump(exclude_unset=True))
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@app.post(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items",
    status_code=201,
    response_model=menuItem,
    summary="Add a menu item",
    description="Adds a new item to the given menu. The item id is assigned by the server.",
    responses={404: {"description": "Menu not found for this restaurant"}, 422: {"description": "Invalid item data"}},
)
async def add_item_to_menu(restaurant_id: int, menu_id: int, new_item: MenuItemCreate):
    item = add_menu_item(restaurant_id, menu_id, new_item)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return item

@app.patch(
    "/restaurants/{restaurant_id}/menus/{menu_id}/items/{item_id}",
    response_model=menuItem,
    summary="Update a menu item",
    description="Updates only the provided fields of an existing menu item.",
    responses={404: {"description": "Menu or menu item not found"}, 422: {"description": "Invalid item data"}},
)
async def update_item_in_menu(restaurant_id: int, menu_id: int, item_id: int, updates: MenuItemUpdate):
    item = update_menu_item(restaurant_id, menu_id, item_id, updates)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@app.post(
    "/customers/{customer_id}/checkout",
    status_code=201,
    response_model=Order,
    summary="Check out a customer's cart",
    description="Validates the customer's cart for the restaurant against current restaurant and menu data, recalculates prices "
                "and the total, saves an order, and only then clears the cart. Nothing is saved if validation fails.",
    responses={404: {"description": "Customer not found or inactive, or the customer has no cart for this restaurant"},
               409: {"description": "Cart cannot be checked out (empty, invalid quantity, restaurant or item missing, item unavailable)"}},
)
async def checkout_route(customer_id: int, restaurant_id: int, customer=Depends(require_customer_ownership)):
    try:
        return checkout(customer_id, restaurant_id)
    except (CustomerNotFound, CartNotFound) as error:
        raise HTTPException(status_code=404, detail=str(error))
    except CheckoutError as error:
        raise HTTPException(status_code=409, detail=str(error))

@app.post("/auth/login", response_model=Token)
def login(credentials: LoginRequest):

    customer = authenticate_user(
        credentials.email,
        credentials.password
    )

    if customer is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    token = create_access_token(customer["customerId"]) 
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/auth/me")
def get_my_account(customer=Depends(get_current_user)):
    return {
        "customerId": customer["customerId"],
        "name": customer["name"],
        "email": customer["email"]
    }

@app.get(
    "/orders/{order_id}",
    response_model=Order,
    summary="Retrieve an order",
    description="Returns a single order by its ID.",
    responses={404: {"description": "Order not found"}},
)
async def get_order_route(order_id: int):
    order = retrieve_order(order_id)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@app.get(
    "/customers/{customer_id}/orders",
    response_model=OrdersResponse,
    summary="Retrieve a customer's orders",
    description="Returns all orders associated with a customer.",
)
async def get_customer_orders_route(customer_id: int):
    orders = retrieve_customer_orders(customer_id)

    return {"orders": orders}

# Basic frontend, served from the same origin as the API (open http://127.0.0.1:8000/ui/)
app.mount("/ui", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="ui")
