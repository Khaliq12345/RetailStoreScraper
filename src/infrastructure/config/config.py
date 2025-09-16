import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    EEZLY_EMAIL = os.getenv("EEZLY_EMAIL")
    EEZLY_PASSWORD = os.getenv("EEZLY_PASSWORD")

    # aws
    bucket_name = os.getenv("BUCKET_NAME")
    access_key = os.getenv("ACCESS_KEY")
    secret_key = os.getenv("SECRET_KEY")
    beta_bucket = os.getenv("BETA_BUCKET")
    prod_bucket = os.getenv("PROD_BUCKET")
