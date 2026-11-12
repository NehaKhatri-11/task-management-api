import os
from pymongo import MongoClient

# Get MongoDB connection string from environment
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Connect to MongoDB
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)

# Select database
db = client["task_management_db"]

# Select collections
users_collection = db["users"]
tasks_collection = db["tasks"]
revoked_tokens_collection = db["revoked_tokens"]

# Test MongoDB connection
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")

except Exception as e:
    print("MongoDB connection failed:", e)
    raise


# from pymongo import MongoClient

# # Connect to MongoDB
# client = MongoClient("mongodb://localhost:27017/")

# # Select database
# db = client["task_management_db"]

# # Select the connections
# users_collection = db["users"]
# tasks_collection = db["tasks"]
# revoked_tokens_collection = db["revoked_tokens"]

# # Test MongoDB connection
# try:
#     client.admin.command("ping")
#     print("MongoDB connected successfully!")

# except Exception as e:
#     print("MongoDB connection failed:", e)

