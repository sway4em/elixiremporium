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

class CreateCartRequest(BaseModel):
    customer_name: str
    character_class: str
    level: int
    time_id: int

class CartCheckout(BaseModel):
    payment: str

# Update visits table
@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Record customer visits.
    """
    print(Fore.RED + f"Calling /visits/{visit_id} endpoint" + Style.RESET_ALL)
    print(Fore.YELLOW + f"visit_id: {visit_id}" + Style.RESET_ALL)
    print(Fore.GREEN + f"customers: {customers}" + Style.RESET_ALL)

    try:
        with db.engine.begin() as connection:

            latest_time = connection.execute(
                text("""
                    SELECT id FROM time
                    ORDER BY id DESC
                    LIMIT 1
                """)
            ).mappings().fetchone()

            if not latest_time:
                raise HTTPException(status_code=500, detail="No time entries available.")

            current_time_id = latest_time["id"]
            print(Fore.BLUE + f"Current time_id: {current_time_id}" + Style.RESET_ALL)

            for customer in customers:
                result = connection.execute(
                                text("SELECT id FROM customers WHERE name = :name"),
                                {"name": customer.customer_name}
                            ).mappings().fetchone()
                if result:
                    customer_id = result["id"]
                else:
                    customer_result = connection.execute(
                        text("""
                            INSERT INTO customers (name, class, level)
                            VALUES (:name, :class, :level)
                            RETURNING id
                        """),
                        {
                            "name": customer.customer_name,
                            "class": customer.character_class,
                            "level": customer.level
                        }
                    ).mappings().fetchone()
                    customer_id = customer_result["id"]

                connection.execute(
                    text("""
                        INSERT INTO visits (customer_id, time_id)
                        VALUES (
                            (SELECT id FROM customers WHERE name = :name),
                            :time_id
                        )
                    """),
                    {
                        "name": customer.customer_name,
                        "time_id": current_time_id
                    }
                )

    except Exception as e:
        print(Fore.RED + f"Database error in post_visits: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to record visits.")

    return "OK"

# Generate an empty cart
@router.post("/")
def create_cart(new_cart: Customer):
    print(Fore.RED + "Calling /create_cart endpoint" + Style.RESET_ALL)
    print(Fore.YELLOW + f"new_cart: {new_cart}" + Style.RESET_ALL)

    try:
        with db.engine.begin() as connection:

            latest_time = connection.execute(
                text("""
                    SELECT id FROM time
                    ORDER BY id DESC
                    LIMIT 1
                """)
            ).mappings().fetchone()

            if not latest_time:
                raise HTTPException(status_code=500, detail="No time entries available.")

            current_time_id = latest_time["id"]
            print(Fore.BLUE + f"Current time_id: {current_time_id}" + Style.RESET_ALL)

            cart_result = connection.execute(
                text("""
                    INSERT INTO carts (customer_id, time_id)
                    VALUES (
                        (SELECT id FROM customers WHERE name = :name),
                        :time_id
                    )
                    RETURNING id
                """),
                {
                    "name": new_cart.customer_name,
                    "time_id": current_time_id
                }
            ).mappings().fetchone()

            cart_id = cart_result["id"]
            print(Fore.GREEN + f"Created cart with cart_id: {cart_id}" + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"Database error in create_cart: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to create cart.")

    print(Fore.MAGENTA + f"API called: /create_cart with new_cart: {new_cart} | response: [cart_id: {cart_id}]" + Style.RESET_ALL)
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

# Update cart line items
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Add or update the quantity of an item in the cart.
    """
    print(Fore.RED + f"Calling /{cart_id}/items/{item_sku} endpoint" + Style.RESET_ALL)
    print(Fore.YELLOW + f"cart_id: {cart_id}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"item_sku: {item_sku}" + Style.RESET_ALL)
    print(Fore.GREEN + f"cart_item: {cart_item}" + Style.RESET_ALL)

    try:
        with db.engine.begin() as connection:

            result = connection.execute(
                text("SELECT id FROM recipes WHERE LOWER(name) = :sku"),
                {"sku": item_sku.lower()}
            ).mappings().fetchone()

            if not result:
                raise HTTPException(status_code=400, detail=f"Invalid item SKU: {item_sku}")

            recipe_id = result["id"]

            cart_exists = connection.execute(
                text("SELECT 1 FROM carts WHERE id = :cart_id"),
                {"cart_id": cart_id}
            ).mappings().fetchone()

            if not cart_exists:
                raise HTTPException(status_code=404, detail="Cart not found")

            line_item = connection.execute(
                text("""
                    SELECT id FROM cart_line_items
                    WHERE cart_id = :cart_id AND recipe_id = :recipe_id
                """),
                {"cart_id": cart_id, "recipe_id": recipe_id}
            ).mappings().fetchone()

            if line_item:

                connection.execute(
                    text("""
                        UPDATE cart_line_items
                        SET quantity = :quantity
                        WHERE id = :line_item_id
                    """),
                    {"quantity": cart_item.quantity, "line_item_id": line_item["id"]}
                )
                print(Fore.GREEN + f"Updated quantity for item_sku: {item_sku} in cart_id: {cart_id}" + Style.RESET_ALL)
            else:

                connection.execute(
                    text("""
                        INSERT INTO cart_line_items (cart_id, recipe_id, quantity)
                        VALUES (:cart_id, :recipe_id, :quantity)
                    """),
                    {"cart_id": cart_id, "recipe_id": recipe_id, "quantity": cart_item.quantity}
                )
                print(Fore.GREEN + f"Added item_sku: {item_sku} to cart_id: {cart_id}" + Style.RESET_ALL)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error in set_item_quantity: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to add/update item in cart.")

    print(Fore.MAGENTA + f"API called: /{cart_id}/items/{item_sku} with cart_item: {cart_item} | response: [success: True]" + Style.RESET_ALL)
    return {"success": True}

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    print(Fore.RED + f"Calling /{cart_id}/checkout endpoint" + Style.RESET_ALL)
    print(Fore.YELLOW + f"cart_id: {cart_id}" + Style.RESET_ALL)
    print(Fore.GREEN + f"cart_checkout: {cart_checkout}" + Style.RESET_ALL)

    try:
        with db.engine.begin() as connection:

            cart = connection.execute(
                text("SELECT * FROM carts WHERE id = :cart_id"),
                {"cart_id": cart_id}
            ).mappings().fetchone()

            if not cart:
                raise HTTPException(status_code=404, detail="Cart not found")

            # Get cart items
            cart_items = connection.execute(
                text("""
                    SELECT cli.recipe_id, cli.quantity, p.rp AS price
                    FROM cart_line_items cli
                    JOIN prices p ON cli.recipe_id = p.potion_id
                    WHERE cli.cart_id = :cart_id
                """),
                {"cart_id": cart_id}
            ).mappings().fetchall()

            if not cart_items:
                raise HTTPException(status_code=400, detail="Cart is empty")

            total_potions_bought = 0
            total_gold_paid = 0

            # Calculate total potions bought and total cost
            for item in cart_items:
                stock_result = connection.execute(
                    text("""
                        SELECT quantity as stock
                        FROM current_potion_inventory
                        WHERE recipe_id = :potion_id
                    """),
                    {"potion_id": item["recipe_id"]}
                ).mappings().fetchone()

                current_stock = stock_result["stock"] if stock_result["stock"] else 0

                if item["quantity"] > current_stock:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough stock for potion_id: {item['recipe_id']}. Available: {current_stock}, Requested: {item['quantity']}"
                    )

                total_potions_bought += item["quantity"]
                total_gold_paid += item["quantity"] * item["price"]

            transaction_id = connection.execute(text("""
                INSERT INTO transactions (
                    transaction_type_id,
                    description,
                    external_reference
                )
                VALUES (
                    (SELECT id FROM transaction_types WHERE name = 'POTION_SALE'),
                    :description,
                    :cart_id
                )
                RETURNING id
            """), {
                "description": f"Sale of {total_potions_bought} potions for {total_gold_paid} gold",
                "cart_id": str(cart_id)
            }).scalar()

            for item in cart_items:
                connection.execute(
                    text("""
                        INSERT INTO potion_ledger (transaction_id, recipe_id, change)
                        VALUES (:transaction_id, :recipe_id, :quantity)
                    """),
                    {
                        "transaction_id": transaction_id,
                        "recipe_id": item["recipe_id"],
                        "quantity": -item["quantity"]  # negative because we're reducing stock
                    }
                )
                print(Fore.GREEN + f"Added potion ledger entry for potion_id: {item['recipe_id']} with -{item['quantity']}" + Style.RESET_ALL)

            connection.execute(
                text("""
                    INSERT INTO gold_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """),
                {
                    "transaction_id": transaction_id,
                    "change": total_gold_paid
                }
            )
            print(Fore.GREEN + f"Added gold ledger entry for +{total_gold_paid}" + Style.RESET_ALL)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error in checkout: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to process checkout.")

    print(Fore.BLUE + f"Checkout complete. Total potions: {total_potions_bought}, Total gold paid: {total_gold_paid}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Items bought: {cart_items}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /{cart_id}/checkout with cart_checkout: {cart_checkout} | response: [total_potions_bought: {total_potions_bought}, total_gold_paid: {total_gold_paid}]" + Style.RESET_ALL)
    print(Style.RESET_ALL)
    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid
    }