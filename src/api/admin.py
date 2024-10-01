from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from sqlalchemy import text
from colorama import Fore, Style

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    print(Fore.RED + "Resetting game state" + Style.RESET_ALL)

    with db.engine.begin() as connection:
        connection.execute(
            text("UPDATE global_inventory SET num_green_potions = 0, num_green_ml = 0, gold = 100")
        )
    print(Fore.RED + "Game state reset" + Style.RESET_ALL)
    return "OK"

