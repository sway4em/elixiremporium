from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from colorama import Fore, Style

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

# Get current inventory
@router.get("/audit")
def get_inventory():
    print(Fore.GREEN + "Calling get_inventory()" + Style.RESET_ALL)
    try:
        with db.engine.connect() as connection:

            result_potions = connection.execute(sqlalchemy.text("""
                SELECT SUM(stock) AS number_of_potions
                FROM inventory
            """)).mappings()
            row_potions = result_potions.fetchone()
            number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
            print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)

            result_global = connection.execute(sqlalchemy.text("""
                SELECT num_red_ml, num_green_ml, num_blue_ml, gold
                FROM global_inventory
                LIMIT 1
            """)).mappings()
            row_global = result_global.fetchone()

            if row_global:

                ml_in_barrels = (
                    (row_global['num_red_ml'] if row_global['num_red_ml'] is not None else 0) +
                    (row_global['num_green_ml'] if row_global['num_green_ml'] is not None else 0) +
                    (row_global['num_blue_ml'] if row_global['num_blue_ml'] is not None else 0)
                )
                gold = row_global['gold'] if row_global['gold'] is not None else 0

                print(Fore.GREEN + f"ML in barrels: {ml_in_barrels}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Gold: {gold}" + Style.RESET_ALL)

                print(Fore.MAGENTA + f"API called: /audit | response: {{ 'number_of_potions': {number_of_potions}, 'ml_in_barrels': {ml_in_barrels}, 'gold': {gold} }}" + Style.RESET_ALL)

                return {
                    "number_of_potions": number_of_potions,
                    "ml_in_barrels": ml_in_barrels,
                    "gold": gold
                }
            else:

                print(Fore.RED + f"No inventory data found in global_inventory" + Style.RESET_ALL)
                return {"error": "No inventory data found"}

    except Exception as e:

        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to retrieve inventory data"}

# Get capacity plan
@router.post("/plan")
def get_capacity_plan():
    print(Fore.GREEN + "Calling get_capacity_plan()" + Style.RESET_ALL)

    try:
        with db.engine.connect() as connection:

            result_potions = connection.execute(sqlalchemy.text("""
                SELECT SUM(stock) AS number_of_potions
                FROM inventory
            """)).mappings()
            row_potions = result_potions.fetchone()
            number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
            print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)
            result_global = connection.execute(sqlalchemy.text("""
                SELECT num_red_ml, num_green_ml, num_blue_ml, gold, ml_capacity, potion_capacity
                FROM global_inventory
                LIMIT 1
            """)).mappings()
            row_global = result_global.fetchone()

            if not row_global:
                print(Fore.RED + "No inventory data found in global_inventory" + Style.RESET_ALL)
                return {"error": "No inventory data found"}

            ml_in_barrels = (
                (row_global['num_red_ml'] if row_global['num_red_ml'] is not None else 0) +
                (row_global['num_green_ml'] if row_global['num_green_ml'] is not None else 0) +
                (row_global['num_blue_ml'] if row_global['num_blue_ml'] is not None else 0)
            )

            current_ml_capacity = row_global['ml_capacity'] if row_global['ml_capacity'] is not None else 1
            current_potion_capacity = row_global['potion_capacity'] if row_global['potion_capacity'] is not None else 1
            available_gold = row_global['gold'] if row_global['gold'] is not None else 0

            max_ml_storage = current_ml_capacity
            max_potion_storage = current_potion_capacity

            ml_usage_percentage = (ml_in_barrels / max_ml_storage) * 100 if max_ml_storage > 0 else 100
            potion_usage_percentage = (number_of_potions / max_potion_storage) * 100 if max_potion_storage > 0 else 100

            needed_ml_capacity = 0
            needed_potion_capacity = 0
            total_cost = 0

            print(Fore.BLUE + f"ML in barrels: {ml_in_barrels}, max_ml_storage: {max_ml_storage}, ml_usage_percentage: {ml_usage_percentage}" + Style.RESET_ALL)
            print(Fore.BLUE + f"Number of potions: {number_of_potions}, max_potion_storage: {max_potion_storage}, potion_usage_percentage: {potion_usage_percentage}" + Style.RESET_ALL)
            # If usage is more than 70%, buy more capacity
            if ml_usage_percentage > 70:
                print(Fore.YELLOW + "ML usage is more than 70%" + Style.RESET_ALL)
                needed_ml_capacity = 1
                total_cost += 1000

            if potion_usage_percentage > 70:
                print(Fore.YELLOW + "Potion usage is more than 70%" + Style.RESET_ALL)
                needed_potion_capacity = 1
                total_cost += 1000

            # If total cost is more than available gold, buy the one with the highest usage
            if total_cost > available_gold:
                if available_gold >= 1000:

                    if ml_usage_percentage > potion_usage_percentage:
                        needed_ml_capacity = 1
                        needed_potion_capacity = 0
                    else:
                        needed_ml_capacity = 0
                        needed_potion_capacity = 1
                else:
                    needed_ml_capacity = 0
                    needed_potion_capacity = 0

            response = {
                "potion_capacity": needed_potion_capacity,
                "ml_capacity": needed_ml_capacity
            }

            print(Fore.MAGENTA + f"API called: /plan | response: {response}" + Style.RESET_ALL)
            return response

    except Exception as e:
        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to calculate capacity plan"}

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Deliver purchased capacity
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    print(Fore.GREEN + "Calling deliver_capacity_plan()" + Style.RESET_ALL)

    try:
        with db.engine.connect() as connection:

            total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000

            result = connection.execute(sqlalchemy.text("""
                UPDATE global_inventory
                SET
                    gold = gold - :cost,
                    ml_capacity = ml_capacity + :ml_capacity,
                    potion_capacity = potion_capacity + :potion_capacity
                WHERE gold >= :cost
                RETURNING gold, ml_capacity, potion_capacity
            """), {
                "cost": total_cost,
                "ml_capacity": capacity_purchase.ml_capacity * 10000,
                "potion_capacity": capacity_purchase.potion_capacity * 50
            })

            updated_row = result.fetchone()
            connection.commit()

            if not updated_row:
                print(Fore.RED + "Insufficient gold for capacity purchase" + Style.RESET_ALL)
                return {"error": "Insufficient gold for capacity purchase"}

            print(Fore.MAGENTA + f"API called: /deliver/{order_id} with capacity_purchase: {capacity_purchase} | Order ID: {order_id}, \nresponse: [OK]" + Style.RESET_ALL)
            return "OK"

    except Exception as e:
        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to deliver capacity plan"}
