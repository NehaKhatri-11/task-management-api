
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Query,
    status,
    Request
)
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pwdlib import PasswordHash

from database import (
    users_collection,
    tasks_collection,
    revoked_tokens_collection
)

from schemas import (
    TaskCreate,
    TaskUpdate,
    UserSignup,
    ForgotPasswordRequest,
    ResetPasswordRequest
)


# ==================================================
# ENVIRONMENT CONFIGURATION
# ==================================================

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("TOKEN_EXPIRE_MINUTE", "30")
)

RESET_TOKEN_EXPIRE_MINUTES = 15

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:8000"
)


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Task Management API",
    description="Task Management API with JWT Authentication and MongoDB",
    version="1.0.0"
)


# ==================================================
# FRONTEND CONFIGURATION
# ==================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


# ==================================================
# CORS CONFIGURATION
# ==================================================

allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

frontend_url = FRONTEND_URL.rstrip("/")

if frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==================================================
# PASSWORD HASHING
# ==================================================

password_hash = PasswordHash.recommended()


# ==================================================
# JWT CONFIGURATION
# ==================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def hash_token(token: str):

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ==================================================
# GET CURRENT LOGGED-IN USER
# ==================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if not user_id or not ObjectId.is_valid(user_id):
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    # Check revoked token
    token_hash = hash_token(token)

    revoked_token = revoked_tokens_collection.find_one({
        "token_hash": token_hash
    })

    if revoked_token:
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked. Please login again."
        )

    # Find user
    current_user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not current_user:
        raise credentials_exception

    return current_user


# ==================================================
# ROOT
# ==================================================

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")


# ==================================================
# FRONTEND PAGES
# ==================================================

@app.get("/login.html", include_in_schema=False)
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/signup.html", include_in_schema=False)
def signup_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="signup.html"
    )


@app.get("/tasks.html", include_in_schema=False)
def tasks_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="tasks.html"
    )


@app.get("/forgot_password.html", include_in_schema=False)
def forgot_password_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html"
    )


@app.get("/reset_password.html", include_in_schema=False)
def reset_password_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html"
    )


# ==================================================
# SIGNUP
# ==================================================

@app.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED
)
def signup(user: UserSignup):

    user_data = user.model_dump()

    name = user_data["name"].strip()
    email = str(user_data["email"]).strip().lower()
    password = user_data["password"]

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty"
        )

    # Check existing email
    existing_email = users_collection.find_one({
        "email": email
    })

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check existing name
    existing_name = users_collection.find_one({
        "name": name
    })

    if existing_name:
        raise HTTPException(
            status_code=400,
            detail="Name already registered"
        )

    hashed_password = password_hash.hash(password)

    new_user = {
        "name": name,
        "email": email,
        "password_hash": hashed_password,
        "created_at": datetime.now(timezone.utc)
    }

    result = users_collection.insert_one(new_user)

    print(
        "New user registered:",
        email,
        flush=True
    )

    return {
        "message": "Account created successfully!",
        "user_id": str(result.inserted_id)
    }


# ==================================================
# LOGIN
# ==================================================

@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    # Login using user's name
    name = form_data.username.strip()

    user = users_collection.find_one({
        "name": name
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

    access_token = create_access_token({
        "user_id": str(user["_id"])
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful!"
    }


# ==================================================
# LOGOUT
# ==================================================

@app.post("/auth/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(get_current_user)
):

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc
    )

    revoked_tokens_collection.insert_one({
        "token_hash": hash_token(token),
        "user_id": current_user["_id"],
        "expires_at": expires_at,
        "revoked_at": datetime.now(timezone.utc)
    })

    return {
        "message": "Logout successful!"
    }


# ==================================================
# USER PROFILE
# ==================================================

@app.get("/auth/profile")
def get_profile(
    current_user: dict = Depends(get_current_user)
):

    return {
        "id": str(current_user["_id"]),
        "name": current_user["name"],
        "email": current_user["email"]
    }


# ==================================================
# FORGOT PASSWORD
# ==================================================

@app.post("/auth/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest
):

    print(
        "\n========== FORGOT PASSWORD REQUEST ==========",
        flush=True
    )

    email = str(request.email).strip().lower()

    print("Email received:", email, flush=True)

    user = users_collection.find_one({
        "email": email
    })

    # Do not reveal whether an email is registered
    if not user:

        print("USER NOT FOUND IN MONGODB!", flush=True)
        print("============================================\n", flush=True)

        return {
            "message": (
                "If the email is registered, "
                "a password reset link will be generated."
            )
        }

    print("USER FOUND:", user["email"], flush=True)

    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)

    token_hash = hash_token(reset_token)

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_EXPIRE_MINUTES
    )

    # Store hashed token in MongoDB
    result = users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token_hash": token_hash,
                "reset_token_expires": expires_at
            }
        }
    )

    if result.matched_count == 0:

        raise HTTPException(
            status_code=500,
            detail="Could not generate password reset link"
        )

    reset_link = (
        f"{FRONTEND_URL.rstrip('/')}"
        f"/reset_password.html?token={reset_token}"
    )

    # Print link in VS Code terminal or Render logs
    print(
        "\n========== PASSWORD RESET LINK ==========",
        flush=True
    )

    print(reset_link, flush=True)

    print(
        f"Token expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes.",
        flush=True
    )

    print(
        "==========================================\n",
        flush=True
    )

    return {
        "message": (
            "If the email is registered, "
            "a password reset link will be generated."
        )
    }


# ==================================================
# RESET PASSWORD
# ==================================================

@app.post("/auth/reset-password")
def reset_password(
    request: ResetPasswordRequest
):

    token_hash = hash_token(request.token)

    user = users_collection.find_one({
        "reset_token_hash": token_hash
    })

    if not user:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset link"
        )

    expires_at = user.get("reset_token_expires")

    if not expires_at:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset link"
        )

    # Handle MongoDB datetime
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at <= datetime.now(timezone.utc):

        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$unset": {
                    "reset_token_hash": "",
                    "reset_token_expires": ""
                }
            }
        )

        raise HTTPException(
            status_code=400,
            detail="Reset link has expired"
        )

    # Hash new password
    new_hashed_password = password_hash.hash(
        request.new_password
    )

    users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": new_hashed_password
            },
            "$unset": {
                "reset_token_hash": "",
                "reset_token_expires": ""
            }
        }
    )

    return {
        "message": "Password reset successfully! Please login."
    }


# ==================================================
# CREATE TASK
# ==================================================

@app.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED
)
def create_task(
    task: TaskCreate,
    current_user: dict = Depends(get_current_user)
):

    task_data = task.model_dump()

    new_task = {
        **task_data,
        "user_id": current_user["_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    result = tasks_collection.insert_one(new_task)

    created_task = tasks_collection.find_one({
        "_id": result.inserted_id
    })

    created_task["id"] = str(created_task.pop("_id"))
    created_task["user_id"] = str(created_task["user_id"])

    return {
        "message": "Task created successfully!",
        "task": created_task
    }


# ==================================================
# GET ALL TASKS
# SEARCH, FILTER, SORT AND PAGINATION
# ==================================================

@app.get("/tasks")
def get_all_tasks(
    status_filter: str = Query(default=None),
    search: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1, le=100),
    sort_order: int = Query(default=-1),
    current_user: dict = Depends(get_current_user)
):

    if sort_order not in [1, -1]:

        raise HTTPException(
            status_code=400,
            detail="sort_order must be 1 or -1"
        )

    query = {
        "user_id": current_user["_id"]
    }

    # Filter by status
    if status_filter:
        query["status"] = status_filter

    # Search title and description
    if search:

        query["$or"] = [
            {
                "title": {
                    "$regex": search,
                    "$options": "i"
                }
            },
            {
                "description": {
                    "$regex": search,
                    "$options": "i"
                }
            }
        ]

    skip = (page - 1) * limit

    total_tasks = tasks_collection.count_documents(query)

    tasks = list(
        tasks_collection.find(query)
        .sort("created_at", sort_order)
        .skip(skip)
        .limit(limit)
    )

    for task in tasks:

        task["id"] = str(task.pop("_id"))
        task["user_id"] = str(task["user_id"])

    total_pages = (total_tasks + limit - 1) // limit

    return {
        "total_tasks": total_tasks,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "tasks": tasks
    }


# ==================================================
# GET TASK BY ID
# ==================================================

@app.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):

        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    task = tasks_collection.find_one({
        "_id": ObjectId(task_id),
        "user_id": current_user["_id"]
    })

    if not task:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task["id"] = str(task.pop("_id"))
    task["user_id"] = str(task["user_id"])

    return task


# ==================================================
# UPDATE TASK
# ==================================================

@app.put("/tasks/{task_id}")
def update_task(
    task_id: str,
    task: TaskUpdate,
    current_user: dict = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):

        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    update_data = task.model_dump(
        exclude_unset=True
    )

    if not update_data:

        raise HTTPException(
            status_code=400,
            detail="No update data provided"
        )

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = tasks_collection.update_one(
        {
            "_id": ObjectId(task_id),
            "user_id": current_user["_id"]
        },
        {
            "$set": update_data
        }
    )

    if result.matched_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    updated_task = tasks_collection.find_one({
        "_id": ObjectId(task_id),
        "user_id": current_user["_id"]
    })

    updated_task["id"] = str(updated_task.pop("_id"))
    updated_task["user_id"] = str(updated_task["user_id"])

    return {
        "message": "Task updated successfully!",
        "task": updated_task
    }


# ==================================================
# DELETE TASK
# ==================================================

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):

    if not ObjectId.is_valid(task_id):

        raise HTTPException(
            status_code=400,
            detail="Invalid task ID"
        )

    result = tasks_collection.delete_one({
        "_id": ObjectId(task_id),
        "user_id": current_user["_id"]
    })

    if result.deleted_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "message": "Task deleted successfully!"
    }
