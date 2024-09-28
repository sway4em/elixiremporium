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

# from fastapi import APIRouter
# import sqlalchemy
# from src import database as db

# router = APIRouter()

@router.get("/audit")
def get_inventory():
    """
    Retrieve the current inventory status from the database.
    """
    print(Fore.GREEN + "Calling get_inventory()" + Style.RESET_ALL)
    sql_to_execute = """
    SELECT num_green_potions, num_green_ml, gold FROM global_inventory
    """
    try:
        with db.engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute)).mappings()
            row = result.fetchone()

            if row:
                print(Fore.GREEN + "Inventory data found" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of potions: {row['num_green_potions']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Number of ml: {row['num_green_ml']}" + Style.RESET_ALL)
                print(Fore.GREEN + f"Gold: {row['gold']}" + Style.RESET_ALL)
                return {
                    "number_of_potions": row['num_green_potions'],
                    "ml_in_barrels": row['num_green_ml'],
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

    return "OK"
