
from pydantic import BaseModel, Field, EmailStr


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = ""
    status: str = "Pending"
    due_date: str = ""


class TaskUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = ""
    status: str = "Pending"
    due_date: str = ""

# User Schema for Signup
class UserSignup(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)

# User Schema for Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)    