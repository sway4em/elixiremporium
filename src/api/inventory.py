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

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """

    print(Fore.GREEN + "Calling get_capacity_plan()" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /plan | response: [potion_capacity: 0, ml_capacity: 0]" + Style.RESET_ALL)
    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """
    print(Fore.MAGENTA + f"API called: /deliver/{order_id} with capacity_purchase: {capacity_purchase} | Order ID: {order_id}, \nresponse: [OK]" + Style.RESET_ALL)
    return "OK"
