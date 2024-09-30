from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style
import requests

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

cart_id = "0"
cart_mapping = {}

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku,
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(Fore.RED + "Calling /visits/{visit_id} endpoint")
    print(Fore.YELLOW + f"visit_id: {visit_id}")
    print(Fore.GREEN + f"customers: {customers}")
    print(Style.RESET_ALL)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global cart_id
    cart_id =str(int(cart_id) + 1)
    cart_mapping[cart_id] = new_cart
    print(Fore.RED + "Calling / create cart endpoint")
    print(Fore.YELLOW + f"new_cart: {new_cart}")
    print(Fore.GREEN + f"cart_id: {cart_id}")
    print(Style.RESET_ALL)

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print(Fore.RED + "Calling /{cart_id}/items/{item_sku} endpoint")
    print(Fore.YELLOW + f"cart_id: {cart_id}")
    print(Fore.YELLOW + f"item_sku: {item_sku}")
    print(Fore.GREEN + f"cart_item: {cart_item}")
    print(Style.RESET_ALL)
    cart_id = str(cart_id)
    if cart_id not in cart_mapping:
        return {"success": False}

    cart = cart_mapping[cart_id]
    if not hasattr(cart, 'items'):
        cart.items = {}

    cart.items[item_sku] = cart_item.quantity

    return {"success": True}

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Handles the checkout process for a specific cart.
    """
    print(Fore.RED + f"Calling /{cart_id}/checkout endpoint")
    print(Fore.YELLOW + f"cart_id: {cart_id}")
    print(Fore.GREEN + f"cart_checkout: {cart_checkout}")
    print(Style.RESET_ALL)

    if cart_id not in cart_mapping:
        raise HTTPException(status_code=404, detail="Cart not found")
    cart = cart_mapping[cart_id]
    if not hasattr(cart, 'items') or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Fetch the catalog
    try:
        catalog_response = requests.get("http://localhost:8501/catalog/")
        catalog_response.raise_for_status()
        catalog = catalog_response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch catalog: {str(e)}")

    # Create a dictionary for quick lookup
    catalog_dict = {item['sku']: item for item in catalog}
    total_potions_bought = 0
    total_gold_paid = 0

    for item_sku, quantity in cart.items.items():
        if item_sku in catalog_dict:
            total_potions_bought += quantity
            total_gold_paid += quantity * catalog_dict[item_sku]["price"]
        else:
            raise HTTPException(status_code=400, detail=f"Invalid item in cart: {item_sku}")

    cart.items.clear()

    print(Fore.BLUE + f"Checkout complete. Total potions: {total_potions_bought}, Total gold: {total_gold_paid}")
    print(Style.RESET_ALL)

    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid
    }
