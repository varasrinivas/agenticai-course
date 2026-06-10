from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ── Tag schemas ──────────────────────────────────────────────
class TagBase(BaseModel):
    name: str
    color: str = "#4285F4"

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    model_config = {"from_attributes": True}


# ── Task schemas ─────────────────────────────────────────────
class TaskBase(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    tag_ids: List[int] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tag_ids: Optional[List[int]] = None

class Task(TaskBase):
    id: int
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: int
    tags: List[Tag] = []
    model_config = {"from_attributes": True}


# ── User schemas ─────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Auth schemas ─────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
