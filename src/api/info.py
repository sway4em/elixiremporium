from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from colorama import Fore, Style

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
    print(Fore.GREEN + f"Day: {timestamp.day}, Hour: {timestamp.hour}" + Style.RESET_ALL)
    return "OK"

