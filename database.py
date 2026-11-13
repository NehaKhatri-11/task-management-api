
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env locally
load_dotenv()

# Get MongoDB connection string
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Connect to MongoDB Atlas
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

# Select database
db = client["task_management_db"]

# Select collections
users_collection = db["users"]
tasks_collection = db["tasks"]
revoked_tokens_collection = db["revoked_tokens"]

# Test connection
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")

except Exception as e:
    print("MongoDB connection failed:", e)
    raise
