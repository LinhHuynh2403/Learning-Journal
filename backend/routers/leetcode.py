from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from backend.database import get_db
from backend.deps import get_current_user
from backend.schemas import LeetCodeLinkIn, ManualSyncIn, RecommendRequest, RecommendResponse, ProblemOut
from backend import crud

router = APIRouter(prefix="/leetcode", tags=["leetcode"])

@router.post("/link")
async def link_leetcode(
    payload: LeetCodeLinkIn,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    await crud.upsert_leetcode_link(db, user["id"], payload.username.strip())
    return {"ok": True, "username": payload.username.strip()}


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
