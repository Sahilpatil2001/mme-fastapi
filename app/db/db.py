from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file

MONGO_URI = os.getenv("MONGO_URI")

# Create async client
client = AsyncIOMotorClient(MONGO_URI)
db = client["mme-mvp"]  # Your DB name

# Collections
users_collection = db["users"]
answers_collection = db["answers"]
core_settings_collection = db["elevenLabsSettings"]
