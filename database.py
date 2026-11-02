from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["task_management_db"]

# Select the connections
users_collection = db["users"]
tasks_collection = db["tasks"]
revoked_tokens_collection = db["revoked_tokens"]

# Test MongoDB connection
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")

except Exception as e:
    print("MongoDB connection failed:", e)