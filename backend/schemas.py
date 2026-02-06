# pydantic schemas
from pydantic import BaseModel
from typing import Optional

# ---------------- User ----------------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

# ---------------- LeetCode Profile ----------------
class LeetCodeProfileCreate(BaseModel):
    leetcode_username: str

class LeetCodeProfileOut(BaseModel):
    id: int
    leetcode_username: str
    last_sync: Optional[str]

    class Config:
        orm_mode = True
