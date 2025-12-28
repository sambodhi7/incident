import os
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # meteres
    DUPLICATE_RADIUS_METERS = 300
    # mins
    DUPLICATE_TIME_WINDOW = 10
    FALSE_REPORT_TIME_LIMIT = 30

