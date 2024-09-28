from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style

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
    """ """
    print(Fore.RED + f"Calling post_deliver_barrels with barrels_delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    total_green_ml = 0
    print(Fore.yellow + f"Iterating through barrels_delivered" + Style.RESET_ALL)

    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 100, 0, 0]:
            print(Fore.YELLOW + f"Barrel: {barrel}" + Style.RESET_ALL)
            total_green_ml += barrel.ml_per_barrel
            print(Fore.YELLOW + f"Total green ml: {total_green_ml}" + Style.RESET_ALL)

    if total_green_ml > 0:
        print(Fore.YELLOW + f"Updating global_inventory with total_green_ml: {total_green_ml}" + Style.RESET_ALL)
        with db.engine.begin() as connection:
            connection.execute(
                text("UPDATE global_inventory SET num_green_ml = num_green_ml + :total_green_ml"),
                {"total_green_ml": total_green_ml}
            )

    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    return {"status": "success", "total_green_ml_delivered": total_green_ml}

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(Fore.RED + f"Calling get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}" + Style.RESET_ALL)
    with db.engine.begin() as connection:
        result = connection.execute(text("SELECT num_green_ml, num_green_potions, gold FROM global_inventory")).mappings()
        inventory = result.fetchone()
        print(Fore.YELLOW + f"Fetching inventory: {inventory}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"Inventory: {inventory}" + Style.RESET_ALL)
        num_green_ml = inventory["num_green_ml"]
        num_green_potions = inventory["num_green_potions"]
        gold = inventory["gold"]

    plan = []
    if num_green_potions < 10:
        print(Fore.YELLOW + f"Low on green potions" + Style.RESET_ALL)
        # Find the smallest green barrel in catalog
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0]:
                if barrel.sku.startswith("SMALL"):
                    plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    break

    print(Fore.RED + f"Wholesale purchase plan: {plan}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Current inventory: {num_green_ml} ml, {num_green_potions} potions, {gold} gold" + Style.RESET_ALL)
    print(Fore.GREEN + f"Wholesale catalog: {wholesale_catalog}" + Style.RESET_ALL)

    return plan

