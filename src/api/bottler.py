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
    print(Fore.RED + f"Calling /bottler/deliver/{order_id}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Delivering potions for order ID: {order_id}" + Style.RESET_ALL)
    total_potions = 0

    # ignore potion type for now
    for potion in potions_delivered:
        total_potions += potion.quantity

    print(Fore.CYAN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
    with db.engine.begin() as connection:
        print(Fore.CYAN + f"Updating global inventory" + Style.RESET_ALL)

        connection.execute(
            text("UPDATE global_inventory SET num_green_potions = num_green_potions + :total_potions, num_green_ml = num_green_ml - :total_potions * 100"),
            {"total_potions": total_potions}
        )


    print(Fore.GREEN + f"Total potions delivered: {total_potions}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /bottler/deliver/{order_id} with potions_delivered: {potions_delivered} | Order ID: {order_id}, \nresponse: [status: success, total_potions_delivered: {total_potions}]" + Style.RESET_ALL)
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

    print(Fore.RED + f"Calling /bottler/plan" + Style.RESET_ALL)
    with db.engine.begin() as connection:
        result = connection.execute(
            text("SELECT num_green_ml FROM global_inventory")
        ).mappings()

        inventory = result.fetchone()
        print(Fore.CYAN + f"Inventory: {inventory}" + Style.RESET_ALL)
        num_green_ml = inventory["num_green_ml"]

        potions_to_bottle = num_green_ml // 100  # 100 ml per potion bottle

    print(Fore.CYAN + f"Inventory retrieved: {num_green_ml} ml" + Style.RESET_ALL)
    print(Fore.CYAN + f"Potions to bottle: {potions_to_bottle}" + Style.RESET_ALL)

    if potions_to_bottle == 0:
        print(Fore.MAGENTA + f"API called: /bottler/plan with response: []" + Style.RESET_ALL)
        return []
    else:
        print(Fore.MAGENTA + f"API called: /bottler/plan with response: [{potions_to_bottle} green potions]" + Style.RESET_ALL)
        return [
            {
                "potion_type": [0, 100, 0, 0], # only green potions for now
                "quantity": potions_to_bottle,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())
