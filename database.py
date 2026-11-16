
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "task_management_db")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = client[DATABASE_NAME]

users_collection = db["users"]
tasks_collection = db["tasks"]
revoked_tokens_collection = db["revoked_tokens"]

try:
    client.admin.command("ping")

    print("MongoDB connected successfully!", flush=True)
    print("Database:", db.name, flush=True)
    print("Users collection:", users_collection.name, flush=True)
    print("MongoDB server:", client.address, flush=True)

except Exception as e:
    print("MongoDB connection failed:", str(e), flush=True)
    raise
