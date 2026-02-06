# functions to interact with DB 
# backend/crud.py
from sqlalchemy.orm import Session
from models import User, LeetCodeProfile
from schemas import UserCreate, LeetCodeProfileCreate
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --------- Users ---------
def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# --------- LeetCode Profile ---------
def link_leetcode_profile(db: Session, user_id: int, profile: LeetCodeProfileCreate):
    db_profile = LeetCodeProfile(
        user_id=user_id,
        leetcode_username=profile.leetcode_username,
        last_sync=datetime.utcnow()
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile
