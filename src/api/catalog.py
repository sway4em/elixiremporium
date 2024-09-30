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
            "SELECT num_green_potions FROM global_inventory"
        )).mappings()
        inventory = result.fetchone()
        print(Fore.GREEN + f"Inventory retrieved: {inventory}" + Style.RESET_ALL)
        num_green_potions = inventory['num_green_potions']
        catalog = [
            {
                "sku": "green_potion_001",
                "name": "Green Potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0]
            }
        ]
        if num_green_potions == 0:
            print(Fore.RED + f"Inventory is empty" + Style.RESET_ALL)
            catalog = []

    print(Fore.GREEN + f"Catalog retrieved: {catalog}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /catalog/ | response: {catalog}" + Style.RESET_ALL)
    return catalog
