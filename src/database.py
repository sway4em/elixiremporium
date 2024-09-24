import os
import dotenv
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()
    print("-"*50)
    print("-"*50)
    print("reading from dotenv")
    print("POSTGRES_URI: ", os.environ.get("POSTGRES_URI"))
    print("-"*50)
    print("-"*50)

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
