from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import aiosqlite

from backend.database import get_db
from backend.deps import get_current_user
from backend.schemas import MentorChatIn, MentorChatOut, MentorRecommendation
from backend import crud
from backend.ollama_client import ollama_chat_json, get_embedding  

router = APIRouter(prefix="/mentor", tags=["mentor"])

@router.post("/chat", response_model=MentorChatOut)
async def mentor_chat(
    payload: MentorChatIn,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    # 1) Pull the user's learning context from SQLite
    history = await crud.get_user_problem_history(db, user["id"], limit=30)
    stats = await crud.get_user_topic_stats(db, user["id"])
    submissions = await crud.get_user_submission_history(db, user["id"], limit=200)

    # ---- Activity metrics (for better plans) ----
    tz = ZoneInfo("America/Los_Angeles")
    now = datetime.now(tz=tz)

    # unique submission dates (local)
    dates = []
    for s in submissions:
        try:
            d = datetime.fromtimestamp(int(s["submitted_at"]), tz=tz).date()
            dates.append(d)
        except Exception:
            continue
    unique_dates = sorted(set(dates), reverse=True)

    # streak = consecutive days starting from most recent submission date
    streak = 0
    if unique_dates:
        cur = unique_dates[0]
        for d in unique_dates:
            if d == cur:
                streak += 1
                cur = cur - timedelta(days=1)
            else:
                break

    ts_now = int(now.timestamp())
    last7 = [s for s in submissions if int(s.get("submitted_at", 0)) >= ts_now - 7 * 86400]
    last30 = [s for s in submissions if int(s.get("submitted_at", 0)) >= ts_now - 30 * 86400]

    recent_solved_slugs = [s["slug"] for s in submissions[:25]]


    # 2) FETCH RELEVANT PROBLEMS FROM QDRANT (New Step)
    # We create a search string based on the user's message and reported weaknesses
    search_query = f"{payload.message} topics: {', '.join(payload.weak_topics)}"
    
    try:
        # Convert search query to a vector using Ollama
        query_vector = await get_embedding(search_query)
        # Find the top matching problems in our vector library
        # vdb_results = search_problems(query_vector, limit=payload.limit)
    except Exception as e:
        # Fallback if Qdrant/Ollama Embedding fails
        vdb_results = []
        print(f"Vector search failed: {e}")

    # Format the Vector DB results for the AI prompt
    vdb_context = "\n".join([
        f"- {res.payload['slug']} ({res.payload.get('difficulty', 'N/A')}): {res.payload.get('description', '')}"
        for res in vdb_results
    ])

    # 3) Build history lines for the prompt
    history_lines = []
    for h in history:
        topics = [t.strip() for t in (h.get("topics") or "").split(",") if t.strip()]
        history_lines.append(f"- {h['slug']} ({h['difficulty']}) status={h['status']} topics={topics}")

    system = (
        "You are an AI LeetCode mentor. Be practical and concise. "
        "Recommend problems based on the user's history, weaknesses, and the retrieved problem library. "
        "Return ONLY JSON with keys: reply, recommendations, next_steps. "
        "recommendations must be a list of {slug, title, difficulty, why}."
    )

    user_prompt = f"""
User message: {payload.message}
Weak topics (self-reported): {payload.weak_topics}
Target difficulty: {payload.target_difficulty}

Relevant Problems Found in Catalog:
{vdb_context if vdb_context else "(No direct catalog matches found)"}

Activity summary:
- last 7 days solved: {len(last7)}
- last 30 days solved: {len(last30)}
- current streak (days): {streak}
- most recent solves (slugs): {recent_solved_slugs}

User topic stats:
- solved counts by topic: {stats.get("solved", {})}
- attempted counts by topic: {stats.get("attempted", {})}

Recent history (most recent first):
{chr(10).join(history_lines) if history_lines else "(no history yet)"}

Rules:
- Use the activity summary to set a realistic weekly plan (number of problems/day, rest days).
- If streak is low or last 7 days is 0, start with smaller, consistent goals.

- Synthesize a plan using the 'Relevant Problems Found in Catalog'.
- Avoid recommending problems that appear as solved in history.
- Output JSON only.
"""

    try:
        obj = await ollama_chat_json(system=system, user=user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

    # 4) Normalize and Clean Response
    reply = obj.get("reply", "")
    recs = obj.get("recommendations", []) or []
    steps = obj.get("next_steps") or obj.get("nextSteps") or []

    cleaned = []
    seen = set()
    solved_slugs = {h["slug"] for h in history if h.get("status") == "solved"}

    for r in recs:
        slug = (r.get("slug") or "").strip()
        if not slug or slug in seen or slug in solved_slugs:
            continue
        
        difficulty = r.get("difficulty") or payload.target_difficulty or "Medium"
        seen.add(slug)
        cleaned.append({
            "slug": slug, 
            "title": r.get("title") or slug, 
            "difficulty": difficulty, 
            "why": r.get("why") or "Good next step."
        })

        # Save into SQLite problems table
        await crud.upsert_problem(db, slug, r.get("title") or slug, difficulty, topics_csv="")

    return MentorChatOut(
        reply=reply,
        recommendations=[MentorRecommendation(**x) for x in cleaned[: payload.limit]],
        next_steps=steps,
    )
