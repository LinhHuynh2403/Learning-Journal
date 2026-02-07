# pydantic schemas
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Literal


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot be longer than 72 bytes.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot be longer than 72 bytes.")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr


# ---------- LeetCode ----------
class LeetCodeLinkIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class ManualSyncIn(BaseModel):
    solved_slugs: List[str] = []
    attempted_slugs: List[str] = []


class ProblemOut(BaseModel):
    slug: str
    title: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    topics: List[str]
    status: Optional[Literal["solved", "attempted", "not_started"]] = None


class RecommendRequest(BaseModel):
    weak_topics: List[str] = []
    difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None
    limit: int = 10


class RecommendResponse(BaseModel):
    recommendations: List[ProblemOut]


# ---------- Mentor (OpenAI) ----------
class MentorChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    weak_topics: List[str] = []
    target_difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None
    limit: int = 5


class MentorRecommendation(BaseModel):
    slug: str
    title: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    why: str


class MentorChatOut(BaseModel):
    reply: str
    recommendations: List[MentorRecommendation] = []
    next_steps: List[str] = []
