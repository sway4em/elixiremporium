from fastapi import APIRouter, Depends, Request, HTTPException
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

# Reset db
@router.post("/reset")
def reset():
    print(Fore.RED + "Resetting game state" + Style.RESET_ALL)
    
    try:
        with db.engine.begin() as connection:
            print(Fore.YELLOW + "Resetting global_inventory" + Style.RESET_ALL)
            # Reset global_inventory
            connection.execute(
                text("""
                    UPDATE global_inventory
                    SET
                        num_red_potions = 0,
                        num_red_ml = 0,
                        num_green_potions = 0,
                        num_green_ml = 0,
                        num_blue_potions = 0,
                        num_blue_ml = 0,
                        num_dark_potions = 0,
                        num_dark_ml = 0,
                        gold = 100,
                        ml_capacity = 10000,
                        potion_capacity = 50
                    WHERE id = 1
                """)
            )
            
            # Set stock of all potions to 0
            print(Fore.YELLOW + "Resetting inventory table" + Style.RESET_ALL)
            connection.execute(
                text("""
                    UPDATE inventory
                    SET
                        stock = 0
                """)
            )

        print(Fore.RED + "Game state reset successfully" + Style.RESET_ALL)
        return {"status": "success", "message": "Game state has been reset."}
    
    except Exception as e:
        print(Fore.RED + f"Error resetting game state: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to reset game state.")

