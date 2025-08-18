from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["mme-mvp"]  # Your DB name
users_collection = db["users"]
answers_collection = db["answers"] 