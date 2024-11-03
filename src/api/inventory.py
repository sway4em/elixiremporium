from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from colorama import Fore, Style

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

# Get current inventory
# @router.get("/audit")
# def get_inventory():
#     print(Fore.GREEN + "Calling get_inventory()" + Style.RESET_ALL)
#     try:
#         with db.engine.connect() as connection:

#             result_potions = connection.execute(sqlalchemy.text("""
#                 SELECT SUM(stock) AS number_of_potions
#                 FROM inventory
#             """)).mappings()
#             row_potions = result_potions.fetchone()
#             number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
#             print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)

#             result_global = connection.execute(sqlalchemy.text("""
#                 SELECT num_red_ml, num_green_ml, num_blue_ml, gold
#                 FROM global_inventory
#                 LIMIT 1
#             """)).mappings()
#             row_global = result_global.fetchone()

#             if row_global:

#                 ml_in_barrels = (
#                     (row_global['num_red_ml'] if row_global['num_red_ml'] is not None else 0) +
#                     (row_global['num_green_ml'] if row_global['num_green_ml'] is not None else 0) +
#                     (row_global['num_blue_ml'] if row_global['num_blue_ml'] is not None else 0)
#                 )
#                 gold = row_global['gold'] if row_global['gold'] is not None else 0

#                 print(Fore.GREEN + f"ML in barrels: {ml_in_barrels}" + Style.RESET_ALL)
#                 print(Fore.GREEN + f"Gold: {gold}" + Style.RESET_ALL)

#                 print(Fore.MAGENTA + f"API called: /audit | response: {{ 'number_of_potions': {number_of_potions}, 'ml_in_barrels': {ml_in_barrels}, 'gold': {gold} }}" + Style.RESET_ALL)

#                 return {
#                     "number_of_potions": number_of_potions,
#                     "ml_in_barrels": ml_in_barrels,
#                     "gold": gold
#                 }
#             else:

#                 print(Fore.RED + f"No inventory data found in global_inventory" + Style.RESET_ALL)
#                 return {"error": "No inventory data found"}

#     except Exception as e:

#         print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
#         return {"error": "Failed to retrieve inventory data"}
@router.get("/audit")
def get_inventory():
    print(Fore.GREEN + "Calling get_inventory()" + Style.RESET_ALL)
    try:
        with db.engine.connect() as connection:

            result_potions = connection.execute(sqlalchemy.text("""
                SELECT * FROM audit_summary
            """)).mappings()
            
            gold, total_ml_in_barrels, total_potions = result_potions.fetchone().values()
            print(Fore.GREEN + f"Number of potions: {total_potions}" + Style.RESET_ALL)
            print(Fore.GREEN + f"ML in barrels: {total_ml_in_barrels}" + Style.RESET_ALL)
            print(Fore.GREEN + f"Gold: {gold}" + Style.RESET_ALL)
            return {
                "number_of_potions": total_potions,
                "ml_in_barrels": total_ml_in_barrels,
                "gold": gold
            }
            # row_potions = result_potions.fetchone()
            # number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
            # print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)

            # result_global = connection.execute(sqlalchemy.text("""
            #     SELECT num_red_ml, num_green_ml, num_blue_ml, gold
            #     FROM global_inventory
            #     LIMIT 1
            # """)).mappings()
            # row_global = result_global.fetchone()

            # if row_global:

            #     ml_in_barrels = (
            #         (row_global['num_red_ml'] if row_global['num_red_ml'] is not None else 0) +
            #         (row_global['num_green_ml'] if row_global['num_green_ml'] is not None else 0) +
            #         (row_global['num_blue_ml'] if row_global['num_blue_ml'] is not None else 0)
            #     )
            #     gold = row_global['gold'] if row_global['gold'] is not None else 0

            #     print(Fore.GREEN + f"ML in barrels: {ml_in_barrels}" + Style.RESET_ALL)
            #     print(Fore.GREEN + f"Gold: {gold}" + Style.RESET_ALL)

            #     print(Fore.MAGENTA + f"API called: /audit | response: {{ 'number_of_potions': {number_of_potions}, 'ml_in_barrels': {ml_in_barrels}, 'gold': {gold} }}" + Style.RESET_ALL)

                # return {
                #     "number_of_potions": number_of_potions,
                #     "ml_in_barrels": ml_in_barrels,
                #     "gold": gold
                # }
            # else:

            #     print(Fore.RED + f"No inventory data found in global_inventory" + Style.RESET_ALL)
            #     return {"error": "No inventory data found"}

    except Exception as e:

        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to retrieve inventory data"}


# Get capacity plan
# @router.post("/plan")
# def get_capacity_plan():
#     print(Fore.GREEN + "Calling get_capacity_plan()" + Style.RESET_ALL)

#     try:
#         with db.engine.connect() as connection:

#             result_potions = connection.execute(sqlalchemy.text("""
#                 SELECT SUM(stock) AS number_of_potions
#                 FROM inventory
#             """)).mappings()
#             row_potions = result_potions.fetchone()
#             number_of_potions = row_potions['number_of_potions'] if row_potions['number_of_potions'] is not None else 0
#             print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)
#             result_global = connection.execute(sqlalchemy.text("""
#                 SELECT num_red_ml, num_green_ml, num_blue_ml, gold, ml_capacity, potion_capacity
#                 FROM global_inventory
#                 LIMIT 1
#             """)).mappings()
#             row_global = result_global.fetchone()

#             if not row_global:
#                 print(Fore.RED + "No inventory data found in global_inventory" + Style.RESET_ALL)
#                 return {"error": "No inventory data found"}

#             ml_in_barrels = (
#                 (row_global['num_red_ml'] if row_global['num_red_ml'] is not None else 0) +
#                 (row_global['num_green_ml'] if row_global['num_green_ml'] is not None else 0) +
#                 (row_global['num_blue_ml'] if row_global['num_blue_ml'] is not None else 0)
#             )

#             current_ml_capacity = row_global['ml_capacity'] if row_global['ml_capacity'] is not None else 1
#             current_potion_capacity = row_global['potion_capacity'] if row_global['potion_capacity'] is not None else 1
#             available_gold = row_global['gold'] if row_global['gold'] is not None else 0

#             max_ml_storage = current_ml_capacity
#             max_potion_storage = current_potion_capacity

#             ml_usage_percentage = (ml_in_barrels / max_ml_storage) * 100 if max_ml_storage > 0 else 100
#             potion_usage_percentage = (number_of_potions / max_potion_storage) * 100 if max_potion_storage > 0 else 100

#             needed_ml_capacity = 0
#             needed_potion_capacity = 0
#             total_cost = 0

#             print(Fore.BLUE + f"ML in barrels: {ml_in_barrels}, max_ml_storage: {max_ml_storage}, ml_usage_percentage: {ml_usage_percentage}" + Style.RESET_ALL)
#             print(Fore.BLUE + f"Number of potions: {number_of_potions}, max_potion_storage: {max_potion_storage}, potion_usage_percentage: {potion_usage_percentage}" + Style.RESET_ALL)
#             # If usage is more than 70%, buy more capacity
#             if ml_usage_percentage > 70:
#                 print(Fore.YELLOW + "ML usage is more than 70%" + Style.RESET_ALL)
#                 needed_ml_capacity = 1
#                 total_cost += 1000
            
#             #force buy ml capacity just for today
#             needed_ml_capacity = 1
#             total_cost = 1000

#             if potion_usage_percentage > 70:
#                 print(Fore.YELLOW + "Potion usage is more than 70%" + Style.RESET_ALL)
#                 needed_potion_capacity = 1
#                 total_cost += 1000

#             # If total cost is more than available gold, buy the one with the highest usage
#             if total_cost > available_gold:
#                 if available_gold >= 1000:

#                     if ml_usage_percentage > potion_usage_percentage:
#                         needed_ml_capacity = 1
#                         needed_potion_capacity = 0
#                     else:
#                         needed_ml_capacity = 0
#                         needed_potion_capacity = 1
#                 else:
#                     needed_ml_capacity = 0
#                     needed_potion_capacity = 0

#             response = {
#                 "potion_capacity": needed_potion_capacity,
#                 "ml_capacity": needed_ml_capacity
#             }

#             print(Fore.MAGENTA + f"API called: /plan | response: {response}" + Style.RESET_ALL)
#             return response

#     except Exception as e:
#         print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
#         return {"error": "Failed to calculate capacity plan"}
@router.post("/plan")
def get_capacity_plan():
    print(Fore.GREEN + "Calling get_capacity_plan()" + Style.RESET_ALL)

    try:
        with db.engine.connect() as connection:
            result_audit = connection.execute(sqlalchemy.text("""
                SELECT gold, total_potions, total_ml_in_barrels FROM audit_summary
            """)).mappings()
            available_gold, number_of_potions, ml_in_barrels = result_audit.fetchone().values()
            print(Fore.GREEN + f"Number of potions: {number_of_potions}" + Style.RESET_ALL)
            print(Fore.GREEN + f"ML in barrels: {ml_in_barrels}" + Style.RESET_ALL)
            print(Fore.GREEN + f"Gold: {available_gold}" + Style.RESET_ALL)
            
            result_capacity = connection.execute(sqlalchemy.text("""
                SELECT ml_capacity, potion_capacity FROM current_capacities
            """)).mappings()
            current_ml_capacity, current_potion_capacity = result_capacity.fetchone().values()

            max_ml_storage = current_ml_capacity
            max_potion_storage = current_potion_capacity

            ml_usage_percentage = (ml_in_barrels / max_ml_storage) * 100 if max_ml_storage > 0 else 100
            potion_usage_percentage = (number_of_potions / max_potion_storage) * 100 if max_potion_storage > 0 else 100

            needed_ml_capacity = 0
            needed_potion_capacity = 0
            total_cost = 0

            print(Fore.BLUE + f"ML in barrels: {ml_in_barrels}, max_ml_storage: {max_ml_storage}, ml_usage_percentage: {ml_usage_percentage}" + Style.RESET_ALL)
            print(Fore.BLUE + f"Number of potions: {number_of_potions}, max_potion_storage: {max_potion_storage}, potion_usage_percentage: {potion_usage_percentage}" + Style.RESET_ALL)
            # If usage is more than 70%, buy more capacity
            if ml_usage_percentage > 70:
                print(Fore.YELLOW + "ML usage is more than 70%" + Style.RESET_ALL)
                needed_ml_capacity = 1
                total_cost += 1000

            if potion_usage_percentage > 70:
                print(Fore.YELLOW + "Potion usage is more than 70%" + Style.RESET_ALL)
                needed_potion_capacity = 1
                total_cost += 1000

            # If total cost is more than available gold, buy the one with the highest usage
            if total_cost > available_gold:
                if available_gold >= 1000:

                    if ml_usage_percentage > potion_usage_percentage:
                        needed_ml_capacity = 1
                        needed_potion_capacity = 0
                    else:
                        needed_ml_capacity = 0
                        needed_potion_capacity = 1
                else:
                    needed_ml_capacity = 0
                    needed_potion_capacity = 0

            response = {
                "potion_capacity": needed_potion_capacity,
                "ml_capacity": needed_ml_capacity
            }

            print(Fore.MAGENTA + f"API called: /plan | response: {response}" + Style.RESET_ALL)
            return response

    except Exception as e:
        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to calculate capacity plan"}
class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Deliver capacity plan
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    print(Fore.GREEN + f"Calling deliver_capacity_plan()\nCapacity to be purchased: {capacity_purchase}" + Style.RESET_ALL)
    try:
        with db.engine.begin() as connection:
            # Calculate values
            total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
            ml_capacity_change = capacity_purchase.ml_capacity * 10000
            potion_capacity_change = capacity_purchase.potion_capacity * 50

            # Check if we have enough gold
            current_gold = connection.execute(sqlalchemy.text("""
                SELECT COALESCE(SUM(change), 100) as gold FROM gold_ledger
            """)).scalar()

            if current_gold < total_cost:
                print(Fore.RED + "Insufficient gold for capacity purchase" + Style.RESET_ALL)
                print(Fore.RED + f"Current gold: {current_gold}, Total cost: {total_cost}" + Style.RESET_ALL)
                return {"error": "Insufficient gold for capacity purchase"}
            
            # Create the transaction
            transaction_id = connection.execute(sqlalchemy.text("""
                INSERT INTO transactions (
                    transaction_type_id,
                    description,
                    external_reference
                )
                VALUES (
                    (SELECT id FROM transaction_types WHERE name = 'CAPACITY_PURCHASE'),
                    :description,
                    :order_id
                )
                RETURNING id
            """), {
                "description": f"Purchased {ml_capacity_change}ml capacity and {potion_capacity_change} potion capacity",
                "order_id": str(order_id)
            }).scalar()

            # Add gold ledger entry
            connection.execute(sqlalchemy.text("""
                INSERT INTO gold_ledger (transaction_id, change)
                VALUES (:transaction_id, :change)
            """), {
                "transaction_id": transaction_id,
                "change": -total_cost
            })

            # Add ml capacity ledger entry
            if ml_capacity_change > 0:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO ml_capacity_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "change": ml_capacity_change
                })

            # Add potion capacity ledger entry
            if potion_capacity_change > 0:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO potion_capacity_ledger (transaction_id, change)
                    VALUES (:transaction_id, :change)
                """), {
                    "transaction_id": transaction_id,
                    "change": potion_capacity_change
                })

            print(Fore.MAGENTA + f"API called: /deliver/{order_id} with capacity_purchase: {capacity_purchase} | Order ID: {order_id}, \nresponse: [OK]" + Style.RESET_ALL)
            return "OK"

    except Exception as e:
        print(Fore.RED + f"Database error: {str(e)}" + Style.RESET_ALL)
        return {"error": "Failed to deliver capacity plan"}