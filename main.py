from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse

from bson import ObjectId
from datetime import datetime, timezone, timedelta

import jwt
import hashlib
import re

from pwdlib import PasswordHash
from database import users_collection, tasks_collection,revoked_tokens_collection
from schemas import UserSignup, TaskCreate, TaskUpdate

app = FastAPI()

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# JWT settings
SECRET_KEY = "my_secret_key_change_later"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

password_hash = PasswordHash.recommended()

# ---------------- PASSWORD AND TOKEN HELPERS ----------------

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "user_id": str(user_id),
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ---------------- AUTHENTICATION ----------------

def get_current_user(token: str = Depends(oauth2_scheme)):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if not user_id or not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        token_hash = hash_token(token)

        # Check whether token is logged out
        revoked = revoked_tokens_collection.find_one({
            "token_hash": token_hash
        })

        if revoked:
            raise HTTPException(
                status_code=401,
                detail="Token has been logged out"
            )

        user = users_collection.find_one({
            "_id": ObjectId(user_id)
        })

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return str(user["_id"])

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

# ---------------- SIGNUP ----------------

@app.post("/auth/signup", status_code=201)
def signup(user: UserSignup):

    existing_user = users_collection.find_one({
        "$or": [
            {"name": user.name},
            {"email": user.email}
        ]
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Name or email already exists"
        )

    new_user = {
        "name": user.name,
        "email": user.email,
        "password_hash": password_hash.hash(user.password),
        "created_at": datetime.now(timezone.utc)
    }

    users_collection.insert_one(new_user)

    return {
        "message": "Account created successfully"
    }

# ---------------- LOGIN ----------------

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    # OAuth2 form sends the name in the username field
    user = users_collection.find_one({
        "name": form_data.username
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid name or password"
        )

    if not password_hash.verify(
        form_data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid name or password"
        )

    access_token = create_access_token(user["_id"])

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ---------------- LOGOUT ----------------

@app.post("/auth/logout")
def logout(token: str = Depends(oauth2_scheme)):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        token_hash = hash_token(token)

        revoked_tokens_collection.update_one(
            {"token_hash": token_hash},
            {
                "$set": {
                    "token_hash": token_hash,
                    "expires_at": datetime.fromtimestamp(
                        payload["exp"],
                        timezone.utc
                    ),
                    "revoked_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )

        return {
            "message": "Logged out successfully"
        }

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

# ---------------- PROFILE ----------------

@app.get("/auth/profile")
def get_profile(user_id: str = Depends(get_current_user)):

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    return {
        "name": user["name"],
        "email": user["email"]
    }

# ---------------- CREATE TASK ----------------

@app.post("/tasks", status_code=201)
def create_task(
    task: TaskCreate,
    user_id: str = Depends(get_current_user)
):

    if task.status not in ["Pending", "In Progress", "Completed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid task status"
        )

    task_data = task.model_dump()

    task_data["user_id"] = ObjectId(user_id)
    task_data["created_at"] = datetime.now(timezone.utc)

    result = tasks_collection.insert_one(task_data)

    return {
        "message": "Task created successfully",
        "task_id": str(result.inserted_id)
    }

# ---------------- GET ALL TASKS ----------------

@app.get("/tasks")
def get_tasks(
    status_filter: str = None,
    search: str = None,
    page: int = 1,
    limit: int = 5,
    sort_order: int = -1,
    user_id: str = Depends(get_current_user)
):

    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be at least 1"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    if sort_order not in [-1, 1]:
        raise HTTPException(
            status_code=400,
            detail="Sort order must be -1 or 1"
        )

    query = {
        "user_id": ObjectId(user_id)
    }

    if status_filter:
        if status_filter not in ["Pending", "In Progress", "Completed"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid task status"
            )

        query["status"] = status_filter

    if search:
        query["title"] = {
            "$regex": re.escape(search),
            "$options": "i"
        }

    total_tasks = tasks_collection.count_documents(query)

    skip = (page - 1) * limit

    cursor = tasks_collection.find(query).sort(
        "created_at",
        sort_order
    ).skip(skip).limit(limit)

    task_list = []

    for task in cursor:
        task["id"] = str(task["_id"])
        task["user_id"] = str(task["user_id"])
        del task["_id"]

        task_list.append(task)

    return {
        "page": page,
        "limit": limit,
        "total_tasks": total_tasks,
        "tasks": task_list
    }

# ---------------- GET TASK BY ID ----------------

@app.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    task = tasks_collection.find_one({
        "_id": ObjectId(task_id),
        "user_id": ObjectId(user_id)
    })

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task["id"] = str(task["_id"])
    task["user_id"] = str(task["user_id"])
    del task["_id"]

    return task

# ---------------- UPDATE TASK ----------------

@app.put("/tasks/{task_id}")
def update_task(
    task_id: str,
    task: TaskUpdate,
    user_id: str = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    if task.status not in ["Pending", "In Progress", "Completed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid task status"
        )

    result = tasks_collection.update_one(
        {
            "_id": ObjectId(task_id),
            "user_id": ObjectId(user_id)
        },
        {
            "$set": task.model_dump()
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "message": "Task updated successfully"
    }

# ---------------- DELETE TASK ----------------

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    result = tasks_collection.delete_one({
        "_id": ObjectId(task_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "message": "Task deleted successfully"
    }
