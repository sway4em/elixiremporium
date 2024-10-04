from fastapi import APIRouter
import sqlalchemy
from src import database as db
import sqlalchemy
from sqlalchemy import text
from colorama import Fore, Style

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print(Fore.RED + f"Calling get_catalog()" + Style.RESET_ALL)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"
        )).mappings()
        inventory = result.fetchone()
        print(Fore.GREEN + f"Inventory retrieved: {inventory}" + Style.RESET_ALL)
        num_red_potions = inventory['num_red_potions']
        num_green_potions = inventory['num_green_potions']
        num_blue_potions = inventory['num_blue_potions']
        catalog = []

        if num_red_potions > 0:
            catalog.append({
                "sku": "red_potion_001",
                "name": "Red Potion",
                "quantity": num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0]
            })
        if num_green_potions > 0:
            catalog.append({
                "sku": "green_potion_001",
                "name": "Green Potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0]
            })

        if num_blue_potions > 0:
            catalog.append({
                "sku": "blue_potion_001",
                "name": "Blue Potion",
                "quantity": num_blue_potions,
                "price": 65,
                "potion_type": [0, 0, 100, 0]
            })

        if not catalog:
            print(Fore.RED + f"Inventory is empty" + Style.RESET_ALL)
    print(Fore.GREEN + f"Catalog retrieved: {catalog}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /catalog/ | response: {catalog}" + Style.RESET_ALL)
    return catalog
