# App 
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.database import init_db
from backend.routers.users import router as users_router
from backend.routers.leetcode import router as leetcode_router
from backend.routers.mentor import router as mentor_router

load_dotenv("backend/.env")

app = FastAPI(title="Learning Journal AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(users_router)
app.include_router(leetcode_router)
app.include_router(mentor_router)

@app.get("/")
async def root():
    return {"ok": True}
