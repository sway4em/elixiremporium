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

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(Fore.RED + f"Calling post_deliver_barrels with barrels_delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    gold_spent = 0
    print(Fore.YELLOW+ f"Iterating through barrels_delivered" + Style.RESET_ALL)

    for barrel in barrels_delivered:
        print(Fore.YELLOW + f"Barrel: {barrel}" + Style.RESET_ALL)
        if barrel.potion_type == [0, 1, 0, 0]:
            print(Fore.YELLOW + f"Green barrel delivered" + Style.RESET_ALL)
            total_green_ml += barrel.ml_per_barrel * barrel.quantity
            print(Fore.YELLOW + f"Total green ml: {total_green_ml}" + Style.RESET_ALL)
        elif barrel.potion_type == [1, 0, 0, 0]:
            print(Fore.YELLOW + f"Red barrel delivered" + Style.RESET_ALL)
            total_red_ml += barrel.ml_per_barrel * barrel.quantity
            print(Fore.YELLOW + f"Total red ml: {total_red_ml}" + Style.RESET_ALL)
        elif barrel.potion_type == [0, 0, 1, 0]:
            print(Fore.YELLOW + f"Blue barrel delivered" + Style.RESET_ALL)
            total_blue_ml += barrel.ml_per_barrel * barrel.quantity
            print(Fore.YELLOW + f"Total blue ml: {total_blue_ml}" + Style.RESET_ALL)
        gold_spent += barrel.price * barrel.quantity

    if total_green_ml > 0 or total_red_ml > 0 or total_blue_ml > 0 or gold_spent > 0:
        print(Fore.YELLOW + f"Updating global_inventory with total_green_ml: {total_green_ml}, total_red_ml: {total_red_ml}, total_blue_ml: {total_blue_ml} and gold_spent: {gold_spent}" + Style.RESET_ALL)
        with db.engine.begin() as connection:
            connection.execute(
                text("UPDATE global_inventory SET num_green_ml = num_green_ml + :total_green_ml, num_red_ml = num_red_ml + :total_red_ml, num_blue_ml = num_blue_ml + :total_blue_ml, gold = gold - :gold_spent"),
                {"total_green_ml": total_green_ml, "total_red_ml": total_red_ml, "total_blue_ml": total_blue_ml, "gold_spent": gold_spent}
            )

    print(Fore.RED + f"Barrels delivered: {barrels_delivered} | Order ID: {order_id}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: post_deliver_barrels with barrels_delivered: {barrels_delivered} | Order ID: {order_id}, \nresponse: [status: success, total_green_ml_delivered: {total_green_ml}, total_red_ml_delivered: {total_red_ml}, total_blue_ml_delivered: {total_blue_ml}, gold_spent: {gold_spent}]" + Style.RESET_ALL)
    return {"status": "success", "total_green_ml_delivered": total_green_ml, "total_red_ml_delivered": total_red_ml, "total_blue_ml_delivered": total_blue_ml, "gold_spent": gold_spent}

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generate a wholesale purchase plan to maximize potion production and profit.
    """
    print(Fore.RED + f"Calling get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}" + Style.RESET_ALL)

    with db.engine.begin() as connection:
        result = connection.execute(text(
            "SELECT num_green_ml, num_green_potions, num_blue_ml, num_blue_potions, num_red_ml, num_red_potions, gold, ml_capacity, potion_capacity FROM global_inventory"
        )).mappings()
        inventory = result.fetchone()
        if not inventory:
            raise HTTPException(status_code=500, detail="Inventory not found.")
        print(Fore.YELLOW + f"Fetching inventory: {inventory}" + Style.RESET_ALL)

        num_green_ml = inventory["num_green_ml"]
        num_green_potions = inventory["num_green_potions"]
        num_red_ml = inventory["num_red_ml"]
        num_red_potions = inventory["num_red_potions"]
        num_blue_ml = inventory["num_blue_ml"]
        num_blue_potions = inventory["num_blue_potions"]
        gold = inventory["gold"]
        ml_capacity = inventory["ml_capacity"]
        potion_capacity = inventory["potion_capacity"]

    potion_ml_required = 100  # ml per potion
    current_total_ml = num_green_ml + num_red_ml + num_blue_ml
    current_total_potions = num_green_potions + num_red_potions + num_blue_potions

    desired_potions = {
        "green": min(max(10 - num_green_potions, 0), potion_capacity - current_total_potions),
        "red": min(max(10 - num_red_potions, 0), potion_capacity - current_total_potions),
        "blue": min(max(10 - num_blue_potions, 0), potion_capacity - current_total_potions),
    }

    additional_ml_needed = {
        "green": min(max(desired_potions["green"] * potion_ml_required - num_green_ml, 0), ml_capacity - current_total_ml),
        "red": min(max(desired_potions["red"] * potion_ml_required - num_red_ml, 0), ml_capacity - current_total_ml),
        "blue": min(max(desired_potions["blue"] * potion_ml_required - num_blue_ml, 0), ml_capacity - current_total_ml),
    }

    print(Fore.YELLOW + f"Additional ML needed: {additional_ml_needed}" + Style.RESET_ALL)

    # sort by cost effectiveness
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
    }

    print(Fore.YELLOW + f"Sorted Catalog by Cost-Effectiveness: {sorted_catalog}" + Style.RESET_ALL)

    plan = []
    total_gold_spent = 0

    def purchase_barrels(potion_type: str, ml_needed: int):
        nonlocal gold, total_gold_spent, current_total_ml
        for barrel in sorted_catalog[potion_type]:
            if ml_needed <= 0 or current_total_ml >= ml_capacity:
                break
            if barrel.quantity <= 0:
                continue  # skip if no more barrels available
            cost_per_ml = barrel.price / barrel.ml_per_barrel
            max_affordable_qty = gold // barrel.price
            max_purchase_qty = min(max_affordable_qty, barrel.quantity)
            if max_purchase_qty <= 0:
                continue

            barrels_needed = (ml_needed + barrel.ml_per_barrel - 1) // barrel.ml_per_barrel
            max_ml_purchase = min(ml_capacity - current_total_ml, ml_needed)
            max_barrels_by_capacity = max_ml_purchase // barrel.ml_per_barrel
            purchase_qty = min(max_purchase_qty, barrels_needed, max_barrels_by_capacity)
            if purchase_qty <= 0:
                continue

            plan.append({"sku": barrel.sku, "quantity": purchase_qty})

            gold -= barrel.price * purchase_qty
            total_gold_spent += barrel.price * purchase_qty
            ml_purchased = barrel.ml_per_barrel * purchase_qty
            ml_needed -= ml_purchased
            current_total_ml += ml_purchased
            print(Fore.CYAN + f"Purchased {purchase_qty} x {barrel.sku} for {barrel.price * purchase_qty} gold" + Style.RESET_ALL)

    # shuffle priority
    potions = ["red", "green", "blue"]
    random.seed(time.time())
    random.shuffle(potions)
    print(Fore.YELLOW + f"Shuffled potion priority: {potions}" + Style.RESET_ALL)
    for potion in potions:
        purchase_barrels(potion, additional_ml_needed[potion])

    print(Fore.RED + f"Wholesale purchase plan: {plan}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Total gold spent: {total_gold_spent} | Gold remaining: {gold}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Current inventory: {num_green_ml} ml, {num_green_potions} potions, {num_red_ml} ml, {num_red_potions} potions, {num_blue_ml} ml, {num_blue_potions} potions, {gold} gold" + Style.RESET_ALL)
    print(Fore.GREEN + f"Wholesale catalog: {wholesale_catalog}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: get_wholesale_purchase_plan with wholesale_catalog: {wholesale_catalog}, \nresponse: {plan}" + Style.RESET_ALL)

    if plan:
        return plan
    else:
        print(Fore.YELLOW + "No purchases made. Plan is empty." + Style.RESET_ALL)

    return plan

