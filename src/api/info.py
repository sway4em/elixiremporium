from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from colorama import Fore, Style
from src import database as db
import sqlalchemy
from sqlalchemy import text

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    with db.engine.connect() as connection:
        query = text("INSERT INTO time (day, hour) VALUES (:day, :hour)")
        connection.execute(query, {"day": timestamp.day, "hour": timestamp.hour})
        connection.commit()
    print(Fore.GREEN + f"Day: {timestamp.day}, Hour: {timestamp.hour}" + Style.RESET_ALL)
    return "OK"

@router.get("/current_time")
def get_current_time():
    with db.engine.connect() as connection:
        query = text("SELECT * FROM time ORDER BY id DESC LIMIT 1")
        result = connection.execute(query).mappings().fetchone()
    print(Fore.GREEN + f"Day: {result['day']}, Hour: {result['hour']}" + Style.RESET_ALL)
    return {"day": result['day'], "hour": result['hour']}
