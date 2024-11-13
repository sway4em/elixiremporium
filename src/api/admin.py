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

@router.post("/reset")
def reset():
    print(Fore.RED + "Resetting game state" + Style.RESET_ALL)
    
    try:
        with db.engine.begin() as connection:
            transaction_id = connection.execute(text("""
                INSERT INTO transactions (
                    transaction_type_id,
                    description
                )
                VALUES (
                    (SELECT id FROM transaction_types WHERE name = 'SHOP_RESET'),
                    'Reset shop to initial state'
                )
                RETURNING id
            """)).scalar()
            print(Fore.YELLOW + f"Created transaction id {transaction_id}" + Style.RESET_ALL)
            current_gold = connection.execute(text(
                "SELECT balance FROM current_gold_balance"
            )).scalar() or 0
            print(Fore.YELLOW + f"Current gold balance: {current_gold}" + Style.RESET_ALL)
            # reset gold to 100
            if current_gold != 100:
                gold_adjustment = 100 - current_gold
                connection.execute(text("""
                    INSERT INTO gold_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "change": gold_adjustment
                })
                print(Fore.YELLOW + f"Reset gold balance with adjustment of {gold_adjustment}" + Style.RESET_ALL)
            
            # reset all ingredient levels to 0
            ingredient_levels = connection.execute(text(
                "SELECT ingredient_type, balance FROM current_ingredient_levels"
            )).mappings().fetchall()
            print(Fore.YELLOW + f"Current ingredient levels: {ingredient_levels}" + Style.RESET_ALL)
            for level in ingredient_levels:
                if level["balance"] != 0:
                    connection.execute(text("""
                        INSERT INTO ingredient_ledger (transaction_id, ingredient_type, change)
                        VALUES (:transaction_id, :ingredient_type, :change)
                    """), {
                        "transaction_id": transaction_id,
                        "ingredient_type": level["ingredient_type"],
                        "change": -level["balance"]
                    })
                    print(Fore.YELLOW + f"Reset {level['ingredient_type']} ingredient to 0" + Style.RESET_ALL)
            
            # reset all potion stock to 0
            potion_stocks = connection.execute(text("""
                SELECT recipe_id, quantity 
                FROM current_potion_inventory 
                WHERE quantity != 0
            """)).mappings().fetchall()
            print(Fore.YELLOW + f"Current potion stocks: {potion_stocks}" + Style.RESET_ALL)
            for stock in potion_stocks:
                connection.execute(text("""
                    INSERT INTO potion_ledger (transaction_id, recipe_id, change)
                    VALUES (:transaction_id, :recipe_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "recipe_id": stock["recipe_id"],
                    "change": -stock["quantity"]
                })
                print(Fore.YELLOW + f"Reset potion id {stock['recipe_id']} stock to 0" + Style.RESET_ALL)
            
            # get current capacities
            current_capacities = connection.execute(text(
                "SELECT ml_capacity, potion_capacity FROM current_capacities"
            )).mappings().fetchone()
            print(Fore.YELLOW + f"Current capacities: {current_capacities}" + Style.RESET_ALL)
            # reset ml capacity to 10000
            if current_capacities["ml_capacity"] != 10000:
                ml_adjustment = 10000 - current_capacities["ml_capacity"]
                connection.execute(text("""
                    INSERT INTO ml_capacity_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "change": ml_adjustment
                })
                print(Fore.YELLOW + f"Reset ml capacity to 10000" + Style.RESET_ALL)
            
            # reset potion capacity to 50
            if current_capacities["potion_capacity"] != 50:
                potion_adjustment = 50 - current_capacities["potion_capacity"]
                connection.execute(text("""
                    INSERT INTO potion_capacity_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "change": potion_adjustment
                })
                print(Fore.YELLOW + f"Reset potion capacity to 50" + Style.RESET_ALL)
                
        print(Fore.GREEN + "Game state reset successfully" + Style.RESET_ALL)
        return {"status": "success", "message": "Game state has been reset."}
    
    except Exception as e:
        print(Fore.RED + f"Error resetting game state: {str(e)}" + Style.RESET_ALL)
        raise HTTPException(status_code=500, detail="Failed to reset game state.")