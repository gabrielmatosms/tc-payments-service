from pymongo import MongoClient

from app.config import settings

mongo_client = MongoClient(
    host=settings.NOSQL_HOST,
    port=settings.NOSQL_PORT,
)

db = mongo_client[settings.NOSQL_DB]

payment_collection = db["payments"] 