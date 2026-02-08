from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
import httpx
import time

from backend.database import get_db
from backend.deps import get_current_user
from backend.schemas import LeetCodeLinkIn, ManualSyncIn, RecommendRequest, RecommendResponse, ProblemOut, LeetCodeMeOut, SyncResponse
from backend import crud
from backend.schemas import LeetCodeLinkRequest
from pydantic import BaseModel

router = APIRouter(prefix="/leetcode", tags=["leetcode"])

import httpx
from fastapi import HTTPException

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

CHECK_USER_QUERY = """
query checkUser($username: String!) {
    matchedUser(username: $username) {
    username
    }
}
"""

async def leetcode_user_exists(username: str) -> bool:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            LEETCODE_GRAPHQL,
            json={"query": CHECK_USER_QUERY, "variables": {"username": username}},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://leetcode.com",
            },
        )
        r.raise_for_status()
        data = r.json()
        user = (data.get("data") or {}).get("matchedUser")
        return user is not None

async def lc_graphql(query: str, variables: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            LEETCODE_GRAPHQL,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://leetcode.com",
            },
        )
        r.raise_for_status()
        return r.json()


@router.get("/me", response_model=LeetCodeMeOut)
async def leetcode_me(
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    username = await crud.get_leetcode_username(db, user["id"])
    last_sync_at = await crud.get_leetcode_last_sync(db, user["id"])

    now = int(time.time())
    last7 = await crud.get_user_submissions_between(db, user["id"], now - 7 * 86400, now)
    last30 = await crud.get_user_submissions_between(db, user["id"], now - 30 * 86400, now)

    return LeetCodeMeOut(
        linked=bool(username),
        username=username,
        last_sync_at=last_sync_at,
        solved_last_7_days=len(last7),
        solved_last_30_days=len(last30),
    )


@router.post("/sync", response_model=SyncResponse)
async def sync_from_leetcode(
    limit: int = 50,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    username = await crud.get_leetcode_username(db, user["id"])
    if not username:
        raise HTTPException(status_code=400, detail="Link LeetCode username first via /leetcode/link")

    payload = await lc_graphql(RECENT_AC_QUERY, {"username": username, "limit": limit})
    items = (payload.get("data") or {}).get("recentAcSubmissionList") or []

    synced_submissions = 0
    updated_statuses = 0

    for it in items:
        slug = it["titleSlug"]
        title = it["title"]
        ts = int(it["timestamp"])

        pid = await crud.get_problem_id_by_slug(db, slug)
        if pid is None:
            pid = await crud.upsert_problem(db, slug, title, "Medium", topics_csv="")

        inserted = await crud.insert_user_submission(db, user["id"], pid, slug, title, "accepted", ts)
        if inserted:
            synced_submissions += 1

        await crud.set_user_problem_status(db, user["id"], pid, "solved")
        updated_statuses += 1

    await crud.set_leetcode_last_sync(db, user["id"])
    last_sync_at = await crud.get_leetcode_last_sync(db, user["id"]) or ""

    return SyncResponse(
        ok=True,
        username=username,
        synced_submissions=synced_submissions,
        updated_statuses=updated_statuses,
        last_sync_at=last_sync_at,
    )


@router.post("/link")
async def link_leetcode(
    payload: LeetCodeLinkRequest,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    username = payload.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    # ✅ validate exists
    if not await leetcode_user_exists(username):
        raise HTTPException(status_code=404, detail="LeetCode username not found")

    await crud.upsert_leetcode_link(db, user["id"], username)
    return {"ok": True, "username": username}

@router.post("/seed")
async def seed_problem_catalog(
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Small starter set (expand anytime)
    starter = [
        ("two-sum", "Two Sum", "Easy", "arrays,hashmap"),
        ("valid-parentheses", "Valid Parentheses", "Easy", "stack"),
        ("merge-two-sorted-lists", "Merge Two Sorted Lists", "Easy", "linked_list"),
        ("binary-tree-inorder-traversal", "Binary Tree Inorder Traversal", "Easy", "trees,dfs"),
        ("number-of-islands", "Number of Islands", "Medium", "graphs,dfs,bfs"),
        ("course-schedule", "Course Schedule", "Medium", "graphs,topological_sort"),
        ("lowest-common-ancestor-of-a-binary-tree", "LCA of a Binary Tree", "Medium", "trees"),
        ("longest-substring-without-repeating-characters", "Longest Substring Without Repeating Characters", "Medium", "sliding_window,hashmap"),
    ]

    for slug, title, diff, topics in starter:
        await crud.upsert_problem(db, slug, title, diff, topics)

    return {"ok": True, "seeded": len(starter)}


@router.post("/sync_manual")
async def sync_manual(
    payload: ManualSyncIn,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Ensure user linked LC first (optional but nice)
    username = await crud.get_leetcode_username(db, user["id"])
    if not username:
        raise HTTPException(status_code=400, detail="Link LeetCode username first via /leetcode/link")

    # Apply statuses
    for slug in payload.solved_slugs:
        pid = await crud.get_problem_id_by_slug(db, slug)
        if pid is not None:
            await crud.set_user_problem_status(db, user["id"], pid, "solved")

    for slug in payload.attempted_slugs:
        pid = await crud.get_problem_id_by_slug(db, slug)
        if pid is not None:
            await crud.set_user_problem_status(db, user["id"], pid, "attempted")

    return {"ok": True, "solved": len(payload.solved_slugs), "attempted": len(payload.attempted_slugs)}


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    payload: RecommendRequest,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    recs = await crud.recommend_problems(
        db=db,
        user_id=user["id"],
        weak_topics=payload.weak_topics,
        difficulty=payload.difficulty,
        limit=payload.limit,
    )

    def to_out(r):
        topics = [t.strip() for t in (r["topics"] or "").split(",") if t.strip()]
        return ProblemOut(
            slug=r["slug"],
            title=r["title"],
            difficulty=r["difficulty"],
            topics=topics,
            status=r.get("status"),
        )

    return {"recommendations": [to_out(r) for r in recs]}
