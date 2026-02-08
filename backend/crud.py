# functions to interact with DB 
# backend/crud.py
from typing import Optional, List, Dict
import aiosqlite
import sqlite3

# ---------- Users ----------
async def get_user_by_email(db: aiosqlite.Connection, email: str) -> Optional[dict]:
    cur = await db.execute("SELECT id, email, hashed_password FROM users WHERE email = ?", (email,))
    row = await cur.fetchone()
    return dict(row) if row else None

async def create_user(db: aiosqlite.Connection, email: str, hashed_password: str) -> dict:
    try:
        cur = await db.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password),
        )
        await db.commit()
        return {"id": cur.lastrowid, "email": email}
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered")



async def get_user_by_id(db: aiosqlite.Connection, user_id: int) -> Optional[dict]:
    cur = await db.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


# ---------- LeetCode link ----------
async def upsert_leetcode_link(db: aiosqlite.Connection, user_id: int, username: str) -> None:
    await db.execute(
        """
        INSERT INTO leetcode_links (user_id, username, updated_at)
        VALUES (?, ?, datetime('now','localtime'))
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            updated_at=datetime('now','localtime');
        """,
        (user_id, username),
    )
    await db.commit()


async def get_leetcode_username(db: aiosqlite.Connection, user_id: int) -> Optional[str]:
    cur = await db.execute("SELECT username FROM leetcode_links WHERE user_id = ?", (user_id,))
    row = await cur.fetchone()
    return row["username"] if row else None


# ---------- Problems catalog ----------
async def upsert_problem(db: aiosqlite.Connection, slug: str, title: str, difficulty: str, topics_csv: str) -> int:
    # insert if not exists
    await db.execute(
        """
        INSERT INTO problems (slug, title, difficulty, topics)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title,
            difficulty=excluded.difficulty,
            topics=excluded.topics;
        """,
        (slug, title, difficulty, topics_csv),
    )
    await db.commit()

    cur = await db.execute("SELECT id FROM problems WHERE slug = ?", (slug,))
    row = await cur.fetchone()
    return int(row["id"])


async def get_problem_id_by_slug(db: aiosqlite.Connection, slug: str) -> Optional[int]:
    cur = await db.execute("SELECT id FROM problems WHERE slug = ?", (slug,))
    row = await cur.fetchone()
    return int(row["id"]) if row else None


async def set_user_problem_status(db: aiosqlite.Connection, user_id: int, problem_id: int, status: str) -> None:
    await db.execute(
        """
        INSERT INTO user_problems (user_id, problem_id, status, last_updated)
        VALUES (?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(user_id, problem_id) DO UPDATE SET
            status=excluded.status,
            last_updated=datetime('now','localtime');
        """,
        (user_id, problem_id, status),
    )
    await db.commit()


async def list_problems_with_status(db: aiosqlite.Connection, user_id: int, limit: int = 50) -> List[Dict]:
    cur = await db.execute(
        """
        SELECT
            p.slug, p.title, p.difficulty, p.topics,
            up.status AS status
        FROM problems p
        LEFT JOIN user_problems up
            ON up.problem_id = p.id AND up.user_id = ?
        ORDER BY p.id DESC
        LIMIT ?;
        """,
        (user_id, limit),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ---------- Recommendations (simple scoring MVP) ----------
async def recommend_problems(
    db: aiosqlite.Connection,
    user_id: int,
    weak_topics: List[str],
    difficulty: Optional[str],
    limit: int,
) -> List[Dict]:
    # Pull a candidate set
    params = []
    where = []
    if difficulty:
        where.append("p.difficulty = ?")
        params.append(difficulty)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    cur = await db.execute(
        f"""
        SELECT
            p.slug, p.title, p.difficulty, p.topics,
            COALESCE(up.status, 'not_started') AS status
        FROM problems p
        LEFT JOIN user_problems up
            ON up.problem_id = p.id AND up.user_id = ?
        {where_sql}
        LIMIT 500;
        """,
        (user_id, *params),
    )
    rows = [dict(r) for r in await cur.fetchall()]

    weak = set(t.strip().lower() for t in weak_topics if t.strip())

    def score(row: Dict) -> int:
        s = 0
        topics = [x.strip().lower() for x in (row["topics"] or "").split(",") if x.strip()]
        if row["status"] == "solved":
            s -= 100
        if weak and any(t in weak for t in topics):
            s += 5
        # Encourage Medium by default if user doesn’t specify
        if not difficulty and row["difficulty"] == "Medium":
            s += 2
        return s

    rows.sort(key=score, reverse=True)
    return rows[:limit]

async def get_user_problem_history(db: aiosqlite.Connection, user_id: int, limit: int = 50) -> List[Dict]:
    """
    Returns latest problems the user interacted with (solved/attempted),
    with topics + difficulty.
    """
    cur = await db.execute(
        """
        SELECT
            p.slug, p.title, p.difficulty, p.topics,
            up.status, up.last_updated
        FROM user_problems up
        JOIN problems p ON p.id = up.problem_id
        WHERE up.user_id = ?
        ORDER BY up.last_updated DESC
        LIMIT ?;
        """,
        (user_id, limit),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_user_topic_stats(db: aiosqlite.Connection, user_id: int) -> Dict:
    """
    Computes simple counts by topic for solved/attempted.
    topics stored as CSV in problems.topics.
    """
    cur = await db.execute(
        """
        SELECT p.topics, up.status
        FROM user_problems up
        JOIN problems p ON p.id = up.problem_id
        WHERE up.user_id = ?;
        """,
        (user_id,),
    )
    rows = await cur.fetchall()

    solved = {}
    attempted = {}

    for r in rows:
        topics = [t.strip().lower() for t in (r["topics"] or "").split(",") if t.strip()]
        target = solved if r["status"] == "solved" else attempted
        for t in topics:
            target[t] = target.get(t, 0) + 1

    return {"solved": solved, "attempted": attempted}


# ---------- LeetCode sync state ----------
async def set_leetcode_last_sync(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute(
        """
        INSERT INTO leetcode_sync_state (user_id, last_sync_at)
        VALUES (?, datetime('now','localtime'))
        ON CONFLICT(user_id) DO UPDATE SET
            last_sync_at=datetime('now','localtime');
        """,
        (user_id,),
    )
    await db.commit()


async def get_leetcode_last_sync(db: aiosqlite.Connection, user_id: int) -> Optional[str]:
    cur = await db.execute("SELECT last_sync_at FROM leetcode_sync_state WHERE user_id = ?", (user_id,))
    row = await cur.fetchone()
    return row["last_sync_at"] if row else None


# ---------- LeetCode submissions ----------
async def insert_user_submission(
    db: aiosqlite.Connection,
    user_id: int,
    problem_id: int,
    title_slug: str,
    title: str,
    status: str,
    submitted_at: int,
) -> bool:
    """Insert a submission row if not already present."""
    cur = await db.execute(
        "SELECT 1 FROM user_submissions WHERE user_id=? AND title_slug=? AND submitted_at=? LIMIT 1;",
        (user_id, title_slug, submitted_at),
    )
    if await cur.fetchone():
        return False

    await db.execute(
        """
        INSERT INTO user_submissions (user_id, problem_id, title_slug, title, status, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (user_id, problem_id, title_slug, title, status, submitted_at),
    )
    await db.commit()
    return True


async def get_user_submission_history(db: aiosqlite.Connection, user_id: int, limit: int = 200) -> List[Dict]:
    cur = await db.execute(
        """
        SELECT title_slug AS slug, title, status, submitted_at, problem_id
        FROM user_submissions
        WHERE user_id = ?
        ORDER BY submitted_at DESC
        LIMIT ?;
        """,
        (user_id, limit),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_user_submissions_between(db: aiosqlite.Connection, user_id: int, start_ts: int, end_ts: int) -> List[Dict]:
    cur = await db.execute(
        """
        SELECT title_slug AS slug, title, status, submitted_at, problem_id
        FROM user_submissions
        WHERE user_id = ? AND submitted_at BETWEEN ? AND ?
        ORDER BY submitted_at DESC;
        """,
        (user_id, start_ts, end_ts),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]
