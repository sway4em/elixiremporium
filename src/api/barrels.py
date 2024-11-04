from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style
import random
import time

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    print(Fore.RED + f"Calling post_deliver_barrels with barrels_delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)

    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_dark_ml = 0
    gold_spent = 0
    print(Fore.YELLOW + f"Iterating through barrels_delivered" + Style.RESET_ALL)

    try:
        with db.engine.begin() as connection:
            for barrel in barrels_delivered:
                print(Fore.YELLOW + f"Barrel: {barrel}" + Style.RESET_ALL)

                red, green, blue, dark = barrel.potion_type

                # very ugly, fix later....
                if [red, green, blue, dark] == [0, 1, 0, 0]:
                    print(Fore.YELLOW + f"Green barrel delivered" + Style.RESET_ALL)
                    total_green_ml += barrel.ml_per_barrel * barrel.quantity
                    print(Fore.YELLOW + f"Total green ml: {total_green_ml}" + Style.RESET_ALL)
                elif [red, green, blue, dark] == [1, 0, 0, 0]:
                    print(Fore.YELLOW + f"Red barrel delivered" + Style.RESET_ALL)
                    total_red_ml += barrel.ml_per_barrel * barrel.quantity
                    print(Fore.YELLOW + f"Total red ml: {total_red_ml}" + Style.RESET_ALL)
                elif [red, green, blue, dark] == [0, 0, 1, 0]:
                    print(Fore.YELLOW + f"Blue barrel delivered" + Style.RESET_ALL)
                    total_blue_ml += barrel.ml_per_barrel * barrel.quantity
                    print(Fore.YELLOW + f"Total blue ml: {total_blue_ml}" + Style.RESET_ALL)
                elif [red, green, blue, dark] == [0, 0, 0, 1]:
                    print(Fore.YELLOW + f"Dark barrel delivered" + Style.RESET_ALL)
                    total_dark_ml += barrel.ml_per_barrel * barrel.quantity
                    print(Fore.YELLOW + f"Total dark ml: {total_dark_ml}" + Style.RESET_ALL)
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid potion_type: {barrel.potion_type} for SKU {barrel.sku}")

                gold_spent += barrel.price * barrel.quantity

            if total_green_ml > 0 or total_red_ml > 0 or total_blue_ml > 0 or total_dark_ml > 0 or gold_spent > 0:
                print(Fore.YELLOW + f"Updating global_inventory with total_green_ml: {total_green_ml}, total_red_ml: {total_red_ml}, total_blue_ml: {total_blue_ml}, total_dark_ml: {total_dark_ml} and gold_spent: {gold_spent}" + Style.RESET_ALL)
                
                transaction_id = connection.execute(sqlalchemy.text("""
                    INSERT INTO transactions (
                        transaction_type_id,
                        description,
                        external_reference
                    )
                    VALUES (
                        (SELECT id FROM transaction_types WHERE name = 'BARREL_PURCHASE'),
                        :description,
                        :order_id
                    )
                    RETURNING id
                """), {
                    "description": f"Purchased barrels: {total_green_ml}ml green, {total_red_ml}ml red, {total_blue_ml}ml blue, {total_dark_ml}ml dark",
                    "order_id": str(order_id)
                }).scalar()
                
                # Record gold spent
                if gold_spent > 0:
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO gold_ledger (transaction_id, change)
                        VALUES (:transaction_id, :change)
                    """), {
                        "transaction_id": transaction_id,
                        "change": -gold_spent
                    })
                    
                # Record ingredient changes
                if total_green_ml > 0:
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                        VALUES (:transaction_id, 'green', :change)
                    """), {
                        "transaction_id": transaction_id,
                        "change": total_green_ml
                    })
                
                if total_red_ml > 0:
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                        VALUES (:transaction_id, 'red', :change)
                    """), {
                        "transaction_id": transaction_id,
                        "change": total_red_ml
                    })

                if total_blue_ml > 0:
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                        VALUES (:transaction_id, 'blue', :change)
                    """), {
                        "transaction_id": transaction_id,
                        "change": total_blue_ml
                    })

                if total_dark_ml > 0:
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                        VALUES (:transaction_id, 'dark', :change)
                    """), {
                        "transaction_id": transaction_id,
                        "change": total_dark_ml
                    })

    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error in post_deliver_barrels: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to deliver barrels.")

    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: post_deliver_barrels with barrels_delivered: {barrels_delivered} | Order ID: {order_id}, \nresponse: [status: success, total_green_ml_delivered: {total_green_ml}, total_red_ml_delivered: {total_red_ml}, total_blue_ml_delivered: {total_blue_ml}, total_dark_ml_delivered: {total_dark_ml}, gold_spent: {gold_spent}]" + Style.RESET_ALL)
    return {
        "status": "success",
        "total_green_ml_delivered": total_green_ml,
        "total_red_ml_delivered": total_red_ml,
        "total_blue_ml_delivered": total_blue_ml,
        "total_dark_ml_delivered": total_dark_ml,
        "gold_spent": gold_spent
    }

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(Fore.RED + f"Calling get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}" + Style.RESET_ALL)

    try:
        with db.engine.connect() as connection:
            ingredient_levels = connection.execute(text(
                "SELECT ingredient_type, balance FROM current_ingredient_levels"
            )).mappings()
            
            if not ingredient_levels:
                raise HTTPException(status_code=500, detail="Inventory not found.")

            ingredient_balances = {row['ingredient_type']: row['balance'] for row in ingredient_levels}

            # Print the fetched inventory
            print(Fore.YELLOW + f"Fetching inventory: {ingredient_balances}" + Style.RESET_ALL)

            # Access the ingredient levels by type
            num_green_ml = ingredient_balances.get("green", 0)
            num_blue_ml = ingredient_balances.get("blue", 0)
            num_red_ml = ingredient_balances.get("red", 0)
            num_dark_ml = ingredient_balances.get("dark", 0)

            
            gold = connection.execute(text(
                "SELECT balance FROM current_gold_balance"
            )).mappings().fetchone()["balance"]

            ml_capacity = connection.execute(text(
                "SELECT ml_capacity FROM current_capacities"
            )).mappings().fetchone()["ml_capacity"]
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error while fetching inventory: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to fetch inventory.")

    # Aim for 25% of each color
    #ml_capacity = ml_capacity - num_green_ml - num_red_ml - num_blue_ml - num_dark_ml
    base_target_ml_per_color = ml_capacity // 4
    ml_needed = {
        "green": max(base_target_ml_per_color - num_green_ml, 0),
        "red": max(base_target_ml_per_color - num_red_ml, 0),
        "blue": max(base_target_ml_per_color - num_blue_ml, 0),
        "dark": max(base_target_ml_per_color - num_dark_ml, 0),
    }

    print(Fore.YELLOW + f"Current inventory: Green ML: {num_green_ml}, Red ML: {num_red_ml}, Blue ML: {num_blue_ml}, Dark ML: {num_dark_ml}, Gold: {gold}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"ML needed per color: {ml_needed}" + Style.RESET_ALL)
    # Sort by cost-effectiveness
    # very ugly, fix later....
    sorted_catalog = {
        "green": sorted(
            [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 1, 0, 0]],
            key=lambda x: x.price / x.ml_per_barrel
        ),
        "red": sorted(
            [barrel for barrel in wholesale_catalog if barrel.potion_type == [1, 0, 0, 0]],
            key=lambda x: x.price / x.ml_per_barrel
        ),
        "blue": sorted(
            [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 0, 1, 0]],
            key=lambda x: x.price / x.ml_per_barrel
        ),
        "dark": sorted(
            [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 0, 0, 1]],
            key=lambda x: x.price / x.ml_per_barrel
        ),
    }

    purchase_plan = []
    total_gold_spent = 0

    def purchase_barrels(color, ml_needed_color):
        nonlocal gold, total_gold_spent
        for barrel in sorted_catalog[color]:
            print(Fore.BLUE + f"Processing {color}" + Style.RESET_ALL)
            print(Fore.BLUE + f"ml_needed_color: {ml_needed_color}" + Style.RESET_ALL)
            if ml_needed_color <= 0:
                break
            if barrel.quantity <= 0:
                continue

            barrels_needed = ml_needed_color // barrel.ml_per_barrel
            print(Fore.BLUE + f"color: {color} ml_needed_color: {ml_needed_color}" + Style.RESET_ALL)
            print(Fore.BLUE + f"barrels_needed: {barrels_needed}" + Style.RESET_ALL)

            max_affordable_qty = gold // barrel.price
            barrels_to_buy = min(barrel.quantity, barrels_needed, max_affordable_qty)
            print(Fore.BLUE + f"max_affordable_qty: {max_affordable_qty}" + Style.RESET_ALL)

            if barrels_to_buy <= 0:
                continue

            ml_provided = barrels_to_buy * barrel.ml_per_barrel

            if ml_provided > ml_needed_color:
                ml_provided = ml_needed_color
                barrels_to_buy = ml_provided // barrel.ml_per_barrel
                if ml_provided % barrel.ml_per_barrel != 0:

                    barrels_to_buy += 1
                    ml_provided = barrels_to_buy * barrel.ml_per_barrel
                    if ml_provided > ml_needed_color:

                        pass

            purchase_plan.append({
                "sku": barrel.sku,
                "quantity": barrels_to_buy
            })

            total_gold_spent += barrels_to_buy * barrel.price
            gold -= barrels_to_buy * barrel.price
            ml_needed[color] -= ml_provided
            ml_needed[color] = max(ml_needed[color], 0)
            print(Fore.BLUE + f"color: {color}, ml_needed[color]: {ml_needed[color]}" + Style.RESET_ALL)
            print(Fore.GREEN + f"Purchased {barrels_to_buy} x {barrel.sku} for {barrels_to_buy * barrel.price} gold, adding {ml_provided} ml to {color}" + Style.RESET_ALL)

            # Break out of the loop if we have enough
            if ml_needed[color] <= 0:
                break

    # colors = ["green", "red", "blue", "dark"]
    # randomize the order of colors to avoid favoring one color
    # random.shuffle(colors)
    
    # buy dark if possible (for today)
    colors = ["green", "red", "blue"]
    random.shuffle(colors)
    colors = ["dark"] + colors
    for color in colors:
        if ml_needed[color] > 0:
            print(Fore.CYAN + f"Processing purchases for {color} (ML needed: {ml_needed[color]})" + Style.RESET_ALL)
            purchase_barrels(color, ml_needed[color])

    print(Fore.MAGENTA + f"Total gold spent: {total_gold_spent}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"Purchase plan: {purchase_plan}" + Style.RESET_ALL)

    print(Fore.YELLOW + f"Current inventory after planning: Green ML: {num_green_ml}, Red ML: {num_red_ml}, Blue ML: {num_blue_ml}, Dark ML: {num_dark_ml}, Gold remaining: {gold}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Wholesale catalog: {wholesale_catalog}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}, \nresponse: {purchase_plan}" + Style.RESET_ALL)

    return purchase_plan