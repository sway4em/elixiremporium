from fastapi import APIRouter
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style
import random
import time
router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    print(Fore.RED + f"Calling get_catalog()" + Style.RESET_ALL)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT
                r.name AS recipe_name,
                cpi.quantity,
                p.rp AS price,
                r.red,
                r.green,
                r.blue,
                r.dark
            FROM current_potion_inventory cpi
            JOIN recipes r ON cpi.recipe_id = r.id
            JOIN prices p ON cpi.recipe_id = p.potion_id
            WHERE cpi.quantity > 0;
        """)).mappings()

        potions = result.fetchall()
        catalog = []
        for potion in potions:
            recipe_name = potion['recipe_name']
            quantity = potion['quantity']
            price = potion['price']
            red = potion['red']
            green = potion['green']
            blue = potion['blue']
            dark = potion['dark']
            sku = recipe_name.lower()
            name_parts = recipe_name.lower().split('_')
            name = ' '.join(word.capitalize() for word in name_parts)
            potion_type = [red, green, blue, dark]
            catalog.append({
                "sku": sku,
                "name": name,
                "quantity": quantity,
                "price": price,
                "potion_type": potion_type
            })

        if not catalog:
            print(Fore.RED + f"Inventory is empty" + Style.RESET_ALL)

    print(Fore.GREEN + f"Catalog retrieved: {catalog}" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"API called: /catalog/ | response: {catalog}" + Style.RESET_ALL)

    # if more than 6 unique items in catalog, return 6 random items
    if len(catalog) > 6:
        shortened_catalog = random.sample(catalog, 6)
        print(Fore.GREEN + f"Shortened catalog: {shortened_catalog}" + Style.RESET_ALL)
        return shortened_catalog
    else:
        return catalog