from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style

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
    """ """
    total_potions = 0
    
    for potion in potions_delivered:
        total_potions += potion.quantity

    with db.engine.begin() as connection:
        connection.execute(
            text("UPDATE global_inventory SET num_green_potions = num_green_potions + :total_potions"),
            {"total_potions": total_potions}
        )
    
    print(f"Potions delivered: {potions_delivered} | Order ID: {order_id}")

    return {"status": "success", "total_potions_delivered": total_potions}

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Current logic: bottle all available green ml into green potions.
    
    with db.engine.begin() as connection:
        result = connection.execute(
            text("SELECT num_green_ml FROM global_inventory")
        )

        inventory = result.fetchone()
        
        num_green_ml = inventory[0]

        potions_to_bottle = num_green_ml // 100  # 100 ml per potion bottle
    
    print(Fore.CYAN + f"Inventory retrieved: {num_green_ml} ml" + Style.RESET_ALL)
    print(Fore.CYAN + f"Potions to bottle: {potions_to_bottle}" + Style.RESET_ALL)
    
    return [
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": potions_to_bottle,
        }
    ]

if __name__ == "__main__":
    print(get_bottle_plan())