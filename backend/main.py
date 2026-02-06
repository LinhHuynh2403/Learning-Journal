#FastAPI app
from fastapi import FastAPI
from database import Base, engine
from routers import users, leetcode

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Learning Journal AI")

app.include_router(users.router)
app.include_router(leetcode.router)
