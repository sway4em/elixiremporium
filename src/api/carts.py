from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style
import requests
import base64
import json
from datetime import datetime

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
    print(Fore.RED + "Calling /search endpoint" + Style.RESET_ALL)
    print(Fore.YELLOW + f"customer_name: {customer_name}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"potion_sku: {potion_sku}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"search_page: {search_page}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"sort_col: {sort_col}" + Style.RESET_ALL)
    try:
        with db.engine.begin() as connection:
            query = """
                SELECT
                    cli.id as line_item_id,
                    r.name as item_sku,
                    c.name as customer_name,
                    cli.quantity * p.rp as line_item_total,
                    t.created_at as timestamp
                FROM cart_line_items cli
                JOIN carts ca ON cli.cart_id = ca.id
                JOIN customers c ON ca.customer_id = c.id
                JOIN recipes r ON cli.recipe_id = r.id
                JOIN prices p ON r.id = p.potion_id
                JOIN time t ON ca.time_id = t.id
                WHERE 1=1
            """

            params = {}

            # add filters if provided
            if customer_name:
                query += " AND LOWER(c.name) LIKE LOWER(:customer_name)"
                params["customer_name"] = f"%{customer_name}%"

            if potion_sku:
                query += " AND LOWER(r.name) LIKE LOWER(:potion_sku)"
                params["potion_sku"] = f"%{potion_sku}%"

            # add sorting
            sort_column_mapping = {
                search_sort_options.customer_name: "c.name",
                search_sort_options.item_sku: "r.name",
                search_sort_options.line_item_total: "line_item_total",
                search_sort_options.timestamp: "t.created_at"
            }

            query += f" ORDER BY {sort_column_mapping[sort_col]} {sort_order.upper()}"

            # get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
            total_count = connection.execute(text(count_query), params).scalar()

            # pagination
            page_size = 5
            if search_page:
                try:
                    cursor_data = json.loads(base64.b64decode(search_page.encode()).decode())
                    offset = cursor_data.get("offset", 0)
                except:
                    offset = 0
            else:
                offset = 0

            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = page_size + 1
            params["offset"] = offset

            results = connection.execute(text(query), params).mappings().fetchall()

            has_next = len(results) > page_size
            actual_results = results[:page_size]

            next_cursor = ""
            if has_next:
                next_cursor = base64.b64encode(
                    json.dumps({"offset": offset + page_size}).encode()
                ).decode()

            previous_cursor = ""
            if offset > 0:
                previous_cursor = base64.b64encode(
                    json.dumps({"offset": max(0, offset - page_size)}).encode()
                ).decode()

            # format results
            # formatted_results = [{
            #     "line_item_id": row["line_item_id"],
            #     "item_sku": row["item_sku"],
            #     "customer_name": row["customer_name"],
            #     "line_item_total": float(row["line_item_total"]),
            #     "timestamp": row["timestamp"].isoformat() + "Z"
            # } for row in actual_results]

            # return {
            #     "previous": previous_cursor,
            #     "next": next_cursor,
            #     "results": formatted_results
            # }
            formatted_results = []
            for row in actual_results:
                timestamp = row["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                elif isinstance(timestamp, datetime):
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

                formatted_results.append({
                    "line_item_id": row["line_item_id"],
                    "item_sku": row["item_sku"],
                    "customer_name": row["customer_name"],
                    "line_item_total": float(row["line_item_total"]),
                    "timestamp": timestamp.isoformat().replace("+00:00", "Z")
                })

            print(Fore.GREEN + f"Total results: {len(formatted_results)}" + Style.RESET_ALL)
            print(Fore.BLUE + f"Next cursor: {next_cursor}" + Style.RESET_ALL)
            print(Fore.BLUE + f"Previous cursor: {previous_cursor}" + Style.RESET_ALL)
            return {
                "previous": previous_cursor,
                "next": next_cursor,
                "results": formatted_results
            }

    except Exception as e:
        print(Fore.RED + f"Database error in search_orders: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to search orders.")

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
    print(Fore.LIGHTBLUE_EX + f"Items bought: {cart_items}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /{cart_id}/checkout with cart_checkout: {cart_checkout} | response: [total_potions_bought: {total_potions_bought}, total_gold_paid: {total_gold_paid}]" + Style.RESET_ALL)
    print(Style.RESET_ALL)
    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid
    }
