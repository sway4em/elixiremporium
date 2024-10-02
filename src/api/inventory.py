from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
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
    """
    Retrieve the current inventory status from the database.
    """
    print(Fore.GREEN + "Calling get_inventory()" + Style.RESET_ALL)
    sql_to_execute = """
    SELECT num_red_potions, num_red_ml, num_blue_potions, num_blue_ml, num_green_potions, num_green_ml, gold FROM global_inventory
    """
    try:
        with db.engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute)).mappings()
            row = result.fetchone()

            if row:
                print(Fore.GREEN + "Inventory data found" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of red potions: {row['num_red_potions']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of green potions: {row['num_green_potions']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of blue potions: {row['num_blue_potions']}" + Style.RESET_ALL)
                print(Fore.GRREN + f"Total number of potions: {row['num_red_potions'] + row['num_green_potions'] + row['num_blue_potions']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of red ml: {row['num_red_ml']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of green ml: {row['num_green_ml']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of blue ml: {row['num_blue_ml']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Gold: {row['gold']}" + Style.RESET_ALL)
                print(Fore.MAGENTA + f"API called: /audit | response: {row}" + Style.RESET_ALL)
                return {
                    "number_of_potions": sum([row['num_red_potions'], row['num_green_potions'], row['num_blue_potions']]),
                    "ml_in_barrels": sum([row['num_red_ml'], row['num_green_ml'], row['num_blue_ml']]),
                    "gold": row['gold']
                }
            else:
                return {"error": "No inventory data found"}
    except Exception as e:
        print(f"Database error: {str(e)}")
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
