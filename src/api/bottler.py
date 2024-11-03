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

# Update inventory with the delivered potions
# @router.post("/deliver/{order_id}")
# def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
#     print(Fore.RED + f"Calling /bottler/deliver/{order_id}" + Style.RESET_ALL)
#     print(Fore.GREEN + f"Delivering potions for order ID: {order_id}" + Style.RESET_ALL)
#     total_potions = 0

#     # Track updates for global_inventory
#     ml_adjustments = {
#         'num_red_ml': 0,
#         'num_green_ml': 0,
#         'num_blue_ml': 0,
#         'num_dark_ml': 0
#     }

#     try:
#         with db.engine.begin() as connection:
#             for potion in potions_delivered:
#                 red, green, blue, dark = potion.potion_type
#                 quantity = potion.quantity

#                 recipe = connection.execute(
#                     text("""
#                         SELECT id, name, red, green, blue, dark
#                         FROM recipes
#                         WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark
#                         LIMIT 1
#                     """),
#                     {
#                         "red": red,
#                         "green": green,
#                         "blue": blue,
#                         "dark": dark
#                     }
#                 ).mappings().fetchone()

#                 if not recipe:
#                     raise HTTPException(status_code=400, detail=f"No matching recipe for potion_type: {potion.potion_type}")

#                 print(Fore.BLUE + f"Processing delivered potion: {recipe['name']} x{quantity}" + Style.RESET_ALL)

#                 ml_adjustments['num_red_ml'] += red * quantity
#                 ml_adjustments['num_green_ml'] += green * quantity
#                 ml_adjustments['num_blue_ml'] += blue * quantity
#                 ml_adjustments['num_dark_ml'] += dark * quantity

#                 # Update inventory stock
#                 connection.execute(
#                     text("""
#                         UPDATE inventory
#                         SET stock = stock + :quantity
#                         WHERE potion_id = :potion_id
#                     """),
#                     {"quantity": quantity, "potion_id": recipe["id"]}
#                 )
#                 print(Fore.CYAN + f"Updated inventory for potion_id {recipe['id']} by +{quantity}" + Style.RESET_ALL)

#                 total_potions += quantity

#             print(Fore.CYAN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
#             print(Fore.CYAN + f"ML adjustments: {ml_adjustments}" + Style.RESET_ALL)

#             # Update num_mls in global_inventory
#             connection.execute(
#                 text("""
#                     UPDATE global_inventory
#                     SET
#                         num_red_ml = num_red_ml - :num_red_ml,
#                         num_green_ml = num_green_ml - :num_green_ml,
#                         num_blue_ml = num_blue_ml - :num_blue_ml,
#                         num_dark_ml = num_dark_ml - :num_dark_ml
#                     WHERE id = 1
#                 """),
#                 ml_adjustments
#             )
#             print(Fore.CYAN + f"Updated global_inventory ml counts based on delivered potions." + Style.RESET_ALL)

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(Fore.RED + f"Database error in post_deliver_bottles: {str(e)}" + Style.RESET_ALL)
#         raise HTTPException(status_code=500, detail="Failed to deliver potions.")

#     print(Fore.GREEN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
#     print(Fore.MAGENTA + f"API called: /bottler/deliver/{order_id} with potions_delivered: {potions_delivered} | Order ID: {order_id}, \nresponse: [status: success, total_potions_delivered: {total_potions}]" + Style.RESET_ALL)

#     return {"status": "success", "total_potions_delivered": total_potions}

# Generate a bottling plan
# @router.post("/plan")
# def get_bottle_plan():
#     print(Fore.RED + f"Calling /bottler/plan" + Style.RESET_ALL)
#     try:
#         with db.engine.connect() as connection:
#             # Fetch num_mls and potion_capacity from global_inventory
#             inventory = connection.execute(
#                 text("""
#                     SELECT ml_capacity, potion_capacity, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml
#                     FROM global_inventory
#                     WHERE id = 1
#                 """)
#             ).mappings().fetchone()

#             if not inventory:
#                 raise HTTPException(status_code=500, detail="Global inventory data not found.")

#             ml_capacity = inventory["ml_capacity"]
#             potion_limit = inventory["potion_capacity"]
            
#             result_potions = connection.execute(sqlalchemy.text("""
#                 SELECT SUM(stock) AS number_of_potions
#                 FROM inventory
#             """)).mappings()
#             row_potions = result_potions.fetchone()
#             number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
#             potion_limit = potion_limit - number_of_potions
#             available_ml = {
#                 'red': inventory["num_red_ml"],
#                 'green': inventory["num_green_ml"],
#                 'blue': inventory["num_blue_ml"],
#                 'dark': inventory["num_dark_ml"]
#             }

#             print(Fore.BLUE + f"Inventory: ml_capacity={ml_capacity}, potion_limit={potion_limit}, available_ml={available_ml}" + Style.RESET_ALL)
            
#             # Fetch all recipes with their current stock and target
#             recipes = connection.execute(
#                 text("""
#                     SELECT r.id, r.name, r.red, r.green, r.blue, r.dark, 
#                            COALESCE(i.stock, 0) as current_stock, 
#                            p.target
#                     FROM recipes r
#                     LEFT JOIN inventory i ON r.id = i.potion_id
#                     LEFT JOIN prices p ON r.id = p.potion_id
#                 """)
#             ).mappings().fetchall()

#             if not recipes:
#                 raise HTTPException(status_code=500, detail="No recipes found.")

#             current_time_seed = int(time.time())
#             random.seed(current_time_seed)
#             recipes_list = list(recipes)  
#             random.shuffle(recipes_list)
#             print(Fore.YELLOW + f"Shuffled recipes with seed {current_time_seed}." + Style.RESET_ALL)

#             bottling_plan = []
#             total_ml_used = 0
#             total_potions_planned = 0
#             can_add_more = True

#             while can_add_more:
#                 can_add_more = False
                
#                 for recipe in recipes_list:
#                     if total_potions_planned >= potion_limit:
#                         can_add_more = False
#                         break
                        
#                     red = recipe["red"]
#                     green = recipe["green"]
#                     blue = recipe["blue"]
#                     dark = recipe["dark"]
#                     current_stock = recipe["current_stock"]
#                     target = recipe["target"]
                    
#                     # Check if current stock is already over target
#                     if current_stock >= target:
#                         print(Fore.YELLOW + f"Skipping {recipe['name']} as current stock is already over target." + Style.RESET_ALL)
#                         continue
                    
#                     # Calculate how many more potions we can make before reaching the target
#                     potions_to_target = target - current_stock
#                     if (available_ml['red'] >= red and 
#                         available_ml['green'] >= green and 
#                         available_ml['blue'] >= blue and 
#                         available_ml['dark'] >= dark and 
#                         total_ml_used + 100 <= ml_capacity and 
#                         total_potions_planned + 1 <= potion_limit and
#                         potions_to_target > 0):
                        
#                         existing_potion = next(
#                             (p for p in bottling_plan 
#                             if p["potion_type"] == [red, green, blue, dark]), 
#                             None
#                         )
                        
#                         if existing_potion:
#                             if total_potions_planned + 1 <= potion_limit and existing_potion["quantity"] < potions_to_target:
#                                 existing_potion["quantity"] += 1
#                                 total_potions_planned += 1
#                                 total_ml_used += 100
                                
#                                 available_ml['red'] -= red
#                                 available_ml['green'] -= green
#                                 available_ml['blue'] -= blue
#                                 available_ml['dark'] -= dark
                                
#                                 print(Fore.GREEN + f"Added 1 more of {recipe['name']} (Type: {red}R, {green}G, {blue}B, {dark}D)" + Style.RESET_ALL)
#                                 can_add_more = True
#                         else:
#                             if total_potions_planned + 1 <= potion_limit:
#                                 bottling_plan.append({
#                                     "potion_type": [red, green, blue, dark],
#                                     "quantity": 1
#                                 })
#                                 total_potions_planned += 1
#                                 total_ml_used += 100
                                
#                                 available_ml['red'] -= red
#                                 available_ml['green'] -= green
#                                 available_ml['blue'] -= blue
#                                 available_ml['dark'] -= dark
                                
#                                 print(Fore.GREEN + f"Added 1 more of {recipe['name']} (Type: {red}R, {green}G, {blue}B, {dark}D)" + Style.RESET_ALL)
#                                 can_add_more = True
#             print(Fore.CYAN + f"Total potions to bottle: {total_potions_planned}, Total ml used: {total_ml_used}" + Style.RESET_ALL)

#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(Fore.RED + f"Database error in get_bottle_plan: {str(e)}" + Style.RESET_ALL)
#         raise HTTPException(status_code=500, detail="Failed to generate bottling plan.")

#     if not bottling_plan:
#         print(Fore.MAGENTA + f"API called: /bottler/plan with response: []" + Style.RESET_ALL)
#         return []

#     print(Fore.MAGENTA + f"API called: /bottler/plan with response: {bottling_plan}" + Style.RESET_ALL)
#     return bottling_plan

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(Fore.RED + f"Calling /bottler/deliver/{order_id}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Delivering potions for order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.CYAN + f"Delivered potions: {potions_delivered}" + Style.RESET_ALL)
    total_potions = 0

    # Track updates for global_inventory
    ml_adjustments = {
        'red': 0,
        'green': 0,
        'blue': 0,
        'dark': 0
    }

    try:
        with db.engine.begin() as connection:
            transaction_id = connection.execute(sqlalchemy.text("""
                INSERT INTO transactions (
                    transaction_type_id,
                    description,
                    external_reference
                )
                VALUES (
                    (SELECT id FROM transaction_types WHERE name = 'POTION_CREATION'),
                    :description,
                    :order_id
                )
                RETURNING id
            """), {
                "description": "Creating potions from ingredients",
                "order_id": str(order_id)
            }).scalar()
            print(Fore.CYAN + f"Created transaction with ID: {transaction_id}" + Style.RESET_ALL)
            for potion in potions_delivered:
                red, green, blue, dark = potion.potion_type
                quantity = potion.quantity
                print(Fore.CYAN + f"Processing potion: {red}R, {green}G, {blue}B, {dark}D x{quantity}" + Style.RESET_ALL)
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
                print(Fore.CYAN + f"ml_adjustments: {ml_adjustments}" + Style.RESET_ALL)
                ml_adjustments['red'] -= red * quantity
                ml_adjustments['green'] -= green * quantity
                ml_adjustments['blue'] -= blue * quantity
                ml_adjustments['dark'] -= dark * quantity

                print(Fore.CYAN + f"ml_adjustments: {ml_adjustments}" + Style.RESET_ALL)

                # Update inventory stock
                # connection.execute(
                #     text("""
                #         UPDATE inventory
                #         SET stock = stock + :quantity
                #         WHERE potion_id = :potion_id
                #     """),
                #     {"quantity": quantity, "potion_id": recipe["id"]}
                # )
                # print(Fore.CYAN + f"Updated inventory for potion_id {recipe['id']} by +{quantity}" + Style.RESET_ALL)

                # total_potions += quantity
                connection.execute(
                    text("""
                        INSERT INTO potion_ledger (transaction_id, recipe_id, change)
                        VALUES (:transaction_id, :recipe_id, :quantity)
                    """),
                    {
                        "transaction_id": transaction_id,
                        "recipe_id": recipe["id"],
                        "quantity": quantity
                    }
                )
                print(Fore.CYAN + f"Added potion ledger entry for potion_id {recipe['id']} with +{quantity}" + Style.RESET_ALL)
                total_potions += quantity

            print(Fore.CYAN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
            print(Fore.CYAN + f"ML adjustments: {ml_adjustments}" + Style.RESET_ALL)

            # Update num_mls in global_inventory
            # connection.execute(
            #     text("""
            #         UPDATE global_inventory
            #         SET
            #             num_red_ml = num_red_ml - :num_red_ml,
            #             num_green_ml = num_green_ml - :num_green_ml,
            #             num_blue_ml = num_blue_ml - :num_blue_ml,
            #             num_dark_ml = num_dark_ml - :num_dark_ml
            #         WHERE id = 1
            #     """),
            #     ml_adjustments
            # )
            for ingredient_type, change in ml_adjustments.items():
                if change != 0:  # Only insert if we used this ingredient
                    connection.execute(
                        text("""
                            INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                            VALUES (:transaction_id, :ingredient_type, :change)
                        """),
                        {
                            "transaction_id": transaction_id,
                            "ingredient_type": ingredient_type,
                            "change": change
                        }
                    )
            print(Fore.CYAN + f"Added ingredient ledger entries for used ingredients." + Style.RESET_ALL)

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
            # Fetch num_mls and potion_capacity from global_inventory
            # inventory = connection.execute(
            #     text("""
            #         SELECT ml_capacity, potion_capacity, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml
            #         FROM global_inventory
            #         WHERE id = 1
            #     """)
            # ).mappings().fetchone()
            capacities = connection.execute(
                text("""
                    SELECT ml_capacity, potion_capacity FROM current_capacities
                """)
            ).mappings().fetchone()

            if not capacities:
                raise HTTPException(status_code=500, detail="Capacities data not found.")

            ml_capacity = capacities["ml_capacity"]
            potion_limit = capacities["potion_capacity"]
            
            print(Fore.YELLOW + f"Capacities: ml_capacity={ml_capacity}, potion_limit={potion_limit}" + Style.RESET_ALL)
            
            # result_potions = connection.execute(sqlalchemy.text("""
            #     SELECT SUM(stock) AS number_of_potions
            #     FROM inventory
            # """)).mappings()
            # row_potions = result_potions.fetchone()
            # number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
            
            number_of_potions = connection.execute(
                text("""
                    SELECT total_potions FROM audit_summary
                """)
            ).mappings().fetchone()["total_potions"]
            print(Fore.YELLOW + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)
            potion_limit = potion_limit - number_of_potions
            print(Fore.YELLOW + f"Adjusted potion limit: {potion_limit}" + Style.RESET_ALL)
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
            
            available_ml = {
                'red': num_red_ml,
                'green': num_green_ml,
                'blue': num_blue_ml,
                'dark': num_dark_ml
            }
            
            # available_ml = {
            #     'red': inventory["num_red_ml"],
            #     'green': inventory["num_green_ml"],
            #     'blue': inventory["num_blue_ml"],
            #     'dark': inventory["num_dark_ml"]
            # }

            print(Fore.BLUE + f"Inventory: ml_capacity={ml_capacity}, potion_limit={potion_limit}, available_ml={available_ml}" + Style.RESET_ALL)
            
            # Fetch all recipes with their current stock and target
            recipes = connection.execute(
                text("""
                     SELECT 
                        r.id, 
                        r.name, 
                        r.red, 
                        r.green, 
                        r.blue, 
                        r.dark,
                        COALESCE(
                            (SELECT SUM(change) 
                            FROM potion_ledger 
                            WHERE recipe_id = r.id), 
                            0
                        ) as current_stock,
                        p.target
                    FROM recipes r
                    LEFT JOIN prices p ON r.id = p.potion_id 
                """)
            ).mappings().fetchall()
            
            print(Fore.YELLOW + f"Recipes: {recipes}" + Style.RESET_ALL)
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
            can_add_more = True

            while can_add_more:
                can_add_more = False
                
                for recipe in recipes_list:
                    if total_potions_planned >= potion_limit:
                        can_add_more = False
                        break
                        
                    red = recipe["red"]
                    green = recipe["green"]
                    blue = recipe["blue"]
                    dark = recipe["dark"]
                    current_stock = recipe["current_stock"]
                    target = recipe["target"]
                    print(Fore.YELLOW + f"Recipe: {recipe}" + Style.RESET_ALL)
                    
                    # Check if current stock is already over target
                    if current_stock >= target:
                        print(Fore.YELLOW + f"Skipping {recipe['name']} as current stock is already over target." + Style.RESET_ALL)
                        continue
                    
                    # Calculate how many more potions we can make before reaching the target
                    potions_to_target = target - current_stock
                    if (available_ml['red'] >= red and 
                        available_ml['green'] >= green and 
                        available_ml['blue'] >= blue and 
                        available_ml['dark'] >= dark and 
                        total_ml_used + 100 <= ml_capacity and 
                        total_potions_planned + 1 <= potion_limit and
                        potions_to_target > 0):
                        
                        existing_potion = next(
                            (p for p in bottling_plan 
                            if p["potion_type"] == [red, green, blue, dark]), 
                            None
                        )
                        
                        if existing_potion:
                            if total_potions_planned + 1 <= potion_limit and existing_potion["quantity"] < potions_to_target:
                                existing_potion["quantity"] += 1
                                total_potions_planned += 1
                                total_ml_used += 100
                                
                                available_ml['red'] -= red
                                available_ml['green'] -= green
                                available_ml['blue'] -= blue
                                available_ml['dark'] -= dark
                                
                                print(Fore.GREEN + f"Added 1 more of {recipe['name']} (Type: {red}R, {green}G, {blue}B, {dark}D)" + Style.RESET_ALL)
                                can_add_more = True
                        else:
                            if total_potions_planned + 1 <= potion_limit:
                                bottling_plan.append({
                                    "potion_type": [red, green, blue, dark],
                                    "quantity": 1
                                })
                                total_potions_planned += 1
                                total_ml_used += 100
                                
                                available_ml['red'] -= red
                                available_ml['green'] -= green
                                available_ml['blue'] -= blue
                                available_ml['dark'] -= dark
                                
                                print(Fore.GREEN + f"Added 1 more of {recipe['name']} (Type: {red}R, {green}G, {blue}B, {dark}D)" + Style.RESET_ALL)
                                can_add_more = True
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