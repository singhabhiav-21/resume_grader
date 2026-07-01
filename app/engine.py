import os
from contextlib import contextmanager
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv

load_dotenv()


def get_engine():
    url = (
        f"postgresql://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME')}"
    )

    return create_engine(url)
