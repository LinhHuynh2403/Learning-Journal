# DB connection
# backend/database.py
import aiosqlite
from typing import AsyncGenerator
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "app.db")


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        # users
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )

        # leetcode link (one per user for MVP)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS leetcode_links (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        # problems catalog
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                topics TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )

        # per-user problem status
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_problems (
                user_id INTEGER NOT NULL,
                problem_id INTEGER NOT NULL,
                status TEXT NOT NULL,              -- "solved" | "attempted" | "not_started"
                last_updated TEXT DEFAULT (datetime('now')),
                PRIMARY KEY(user_id, problem_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
            );
            """
        )

        # reflections
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                problem_id INTEGER NOT NULL,
                notes TEXT NOT NULL,
                ai_feedback TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
            );
            """
        )

        await db.commit()
