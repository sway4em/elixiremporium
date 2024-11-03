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

# Update global_inventory with the delivered barrels
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
                connection.execute(
                    text("""
                        UPDATE global_inventory
                        SET
                            num_green_ml = num_green_ml + :total_green_ml,
                            num_red_ml = num_red_ml + :total_red_ml,
                            num_blue_ml = num_blue_ml + :total_blue_ml,
                            num_dark_ml = num_dark_ml + :total_dark_ml,
                            gold = gold - :gold_spent
                        WHERE id = 1
                    """),
                    {
                        "total_green_ml": total_green_ml,
                        "total_red_ml": total_red_ml,
                        "total_blue_ml": total_blue_ml,
                        "total_dark_ml": total_dark_ml,
                        "gold_spent": gold_spent
                    }
                )

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

# Get the wholesale purchase plan
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(Fore.RED + f"Calling get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}" + Style.RESET_ALL)

    try:
        with db.engine.connect() as connection:

            result = connection.execute(text(
                "SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml, gold, ml_capacity FROM global_inventory WHERE id = 1"
            )).mappings()
            inventory = result.fetchone()
            if not inventory:
                raise HTTPException(status_code=500, detail="Inventory not found.")
            print(Fore.YELLOW + f"Fetching inventory: {inventory}" + Style.RESET_ALL)

            num_green_ml = inventory["num_green_ml"]
            num_red_ml = inventory["num_red_ml"]
            num_blue_ml = inventory["num_blue_ml"]
            num_dark_ml = inventory["num_dark_ml"]
            gold = inventory["gold"]
            ml_capacity = inventory["ml_capacity"]

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
    #ml_needed = {
     #   "green": max(target_ml_per_color - num_green_ml, 0),
      #  "red": max(target_ml_per_color - num_red_ml, 0),
       # "blue": max(target_ml_per_color - num_blue_ml, 0),
        #"dark": max(target_ml_per_color - num_dark_ml, 0),
    #}

    #print(Fore.YELLOW + f"Target ML per color: {target_ml_per_color}" + Style.RESET_ALL)
    #print(Fore.YELLOW + f"ML needed per color: {ml_needed}" + Style.RESET_ALL)

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

    print(Fore.YELLOW + f"Sorted Catalog by Cost-Effectiveness: {sorted_catalog}" + Style.RESET_ALL)

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
