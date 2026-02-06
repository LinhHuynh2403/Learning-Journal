# SQLAlchemy models
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base  # assume we have database.py with Base = declarative_base()

# -----------------------------
# Enums
# -----------------------------
class ProblemStatus(str, enum.Enum):
    not_solved = "not_solved"
    attempted = "attempted"
    solved = "solved"

# -----------------------------
# User table
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    leetcode_profile = relationship("LeetCodeProfile", back_populates="user", uselist=False)
    reflections = relationship("Reflection", back_populates="user")
    ai_feedbacks = relationship("AIFeedback", back_populates="user")
    user_problems = relationship("UserProblem", back_populates="user")


# -----------------------------
# LeetCode Profile
# -----------------------------
class LeetCodeProfile(Base):
    __tablename__ = "leetcode_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    leetcode_username = Column(String, unique=True)
    last_sync = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leetcode_profile")
    # problems will link through UserProblem table


# -----------------------------
# Problem
# -----------------------------
class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    leetcode_id = Column(Integer, unique=True)
    title = Column(String)
    difficulty = Column(String)  # Easy, Medium, Hard
    topic = Column(String)       # Arrays, Graph, DP, etc.

    user_problems = relationship("UserProblem", back_populates="problem")
    reflections = relationship("Reflection", back_populates="problem")


# -----------------------------
# UserProblem (linking table)
# -----------------------------
class UserProblem(Base):
    __tablename__ = "user_problems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"))
    status = Column(Enum(ProblemStatus), default=ProblemStatus.not_solved)
    date_solved = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_problems")
    problem = relationship("Problem", back_populates="user_problems")


# -----------------------------
# Reflection
# -----------------------------
class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=True)  # optional
    text = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reflections")
    problem = relationship("Problem", back_populates="reflections")


# -----------------------------
# AI Feedback
# -----------------------------
class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    feedback_text = Column(String)
    skill_snapshot = Column(JSON)  # e.g. {"arrays":"good","graphs":"weak"}
    date_created = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_feedbacks")
