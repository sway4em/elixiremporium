from fastapi import APIRouter, Depends, HTTPException
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style
import random
import time

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(Fore.RED + f"Calling /bottler/deliver/{order_id}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Delivering potions for order ID: {order_id}" + Style.RESET_ALL)
    total_potions = 0

    ml_adjustments = {
        'num_red_ml': 0,
        'num_green_ml': 0,
        'num_blue_ml': 0,
        'num_dark_ml': 0
    }

    try:
        with db.engine.begin() as connection:
            for potion in potions_delivered:
                red, green, blue, dark = potion.potion_type
                quantity = potion.quantity

                recipe = connection.execute(
                    text("""
                        SELECT id, name, red, green, blue, dark
                        FROM recipes
                        WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark
                        LIMIT 1
                    """),
                    {
                        "red": red,
                        "green": green,
                        "blue": blue,
                        "dark": dark
                    }
                ).mappings().fetchone()

                if not recipe:
                    raise HTTPException(status_code=400, detail=f"No matching recipe for potion_type: {potion.potion_type}")

                print(Fore.BLUE + f"Processing delivered potion: {recipe['name']} x{quantity}" + Style.RESET_ALL)

                ml_adjustments['num_red_ml'] += red * quantity
                ml_adjustments['num_green_ml'] += green * quantity
                ml_adjustments['num_blue_ml'] += blue * quantity
                ml_adjustments['num_dark_ml'] += dark * quantity

                connection.execute(
                    text("""
                        UPDATE inventory
                        SET stock = stock + :quantity
                        WHERE potion_id = :potion_id
                    """),
                    {"quantity": quantity, "potion_id": recipe["id"]}
                )
                print(Fore.CYAN + f"Updated inventory for potion_id {recipe['id']} by +{quantity}" + Style.RESET_ALL)

                total_potions += quantity

            print(Fore.CYAN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
            print(Fore.CYAN + f"ML adjustments: {ml_adjustments}" + Style.RESET_ALL)

            connection.execute(
                text("""
                    UPDATE global_inventory
                    SET
                        num_red_ml = num_red_ml - :num_red_ml,
                        num_green_ml = num_green_ml - :num_green_ml,
                        num_blue_ml = num_blue_ml - :num_blue_ml,
                        num_dark_ml = num_dark_ml - :num_dark_ml
                    WHERE id = 1
                """),
                ml_adjustments
            )
            print(Fore.CYAN + f"Updated global_inventory ml counts based on delivered potions." + Style.RESET_ALL)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error in post_deliver_bottles: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to deliver potions.")

    print(Fore.GREEN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /bottler/deliver/{order_id} with potions_delivered: {potions_delivered} | Order ID: {order_id}, \nresponse: [status: success, total_potions_delivered: {total_potions}]" + Style.RESET_ALL)

    return {"status": "success", "total_potions_delivered": total_potions}

@router.post("/plan")
def get_bottle_plan():
    print(Fore.RED + f"Calling /bottler/plan" + Style.RESET_ALL)
    try:
        with db.engine.connect() as connection:

            inventory = connection.execute(
                text("""
                    SELECT ml_capacity, potion_capacity, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml
                    FROM global_inventory
                    WHERE id = 1
                """)
            ).mappings().fetchone()

            if not inventory:
                raise HTTPException(status_code=500, detail="Global inventory data not found.")

            ml_capacity = inventory["ml_capacity"]
            potion_limit = inventory["potion_capacity"]
            available_ml = {
                'red': inventory["num_red_ml"],
                'green': inventory["num_green_ml"],
                'blue': inventory["num_blue_ml"],
                'dark': inventory["num_dark_ml"]
            }

            print(Fore.BLUE + f"Inventory: ml_capacity={ml_capacity}, potion_limit={potion_limit}, available_ml={available_ml}" + Style.RESET_ALL)

            recipes = connection.execute(
                text("""
                    SELECT id, name, red, green, blue, dark
                    FROM recipes
                """)
            ).mappings().fetchall()

            if not recipes:
                raise HTTPException(status_code=500, detail="No recipes found.")

            current_time_seed = int(time.time())
            random.seed(current_time_seed)
            recipes_list = list(recipes)  
            random.shuffle(recipes_list)
            print(Fore.YELLOW + f"Shuffled recipes with seed {current_time_seed}." + Style.RESET_ALL)

            bottling_plan = []
            total_ml_used = 0
            total_potions_planned = 0

            for recipe in recipes_list:
                red = recipe["red"]
                green = recipe["green"]
                blue = recipe["blue"]
                dark = recipe["dark"]

                max_bottles_red = available_ml['red'] // red if red > 0 else float('inf')
                max_bottles_green = available_ml['green'] // green if green > 0 else float('inf')
                max_bottles_blue = available_ml['blue'] // blue if blue > 0 else float('inf')
                max_bottles_dark = available_ml['dark'] // dark if dark > 0 else float('inf')

                max_bottles = min(max_bottles_red, max_bottles_green, max_bottles_blue, max_bottles_dark)

                if max_bottles == 0:
                    continue  

                remaining_ml_capacity = ml_capacity - total_ml_used
                remaining_potion_limit = potion_limit - total_potions_planned

                bottles_fit_ml = remaining_ml_capacity // 100
                bottles_to_make = min(max_bottles, bottles_fit_ml, remaining_potion_limit)

                if bottles_to_make <= 0:
                    break  

                bottling_plan.append({
                    "potion_type": [red, green, blue, dark],
                    "quantity": bottles_to_make
                })

                total_ml_used += bottles_to_make * 100
                total_potions_planned += bottles_to_make

                available_ml['red'] -= red * bottles_to_make
                available_ml['green'] -= green * bottles_to_make
                available_ml['blue'] -= blue * bottles_to_make
                available_ml['dark'] -= dark * bottles_to_make

                print(Fore.GREEN + f"Planned to bottle {bottles_to_make} of {recipe['name']} (Type: {red}R, {green}G, {blue}B, {dark}D)" + Style.RESET_ALL)

                if total_ml_used >= ml_capacity or total_potions_planned >= potion_limit:
                    break

            print(Fore.CYAN + f"Total potions to bottle: {total_potions_planned}, Total ml used: {total_ml_used}" + Style.RESET_ALL)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(Fore.RED + f"Database error in get_bottle_plan: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to generate bottling plan.")

    if not bottling_plan:
        print(Fore.MAGENTA + f"API called: /bottler/plan with response: []" + Style.RESET_ALL)
        return []

    print(Fore.MAGENTA + f"API called: /bottler/plan with response: {bottling_plan}" + Style.RESET_ALL)
    return bottling_plan

if __name__ == "__main__":
    print(get_bottle_plan())