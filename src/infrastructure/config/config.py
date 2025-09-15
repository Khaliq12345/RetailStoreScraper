import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    EEZLY_EMAIL = os.getenv("EEZLY_EMAIL")
    EEZLY_PASSWORD = os.getenv("EEZLY_PASSWORD")
