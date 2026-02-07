# backend/routers/mentor.py
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from backend.database import get_db
from backend.deps import get_current_user
from backend.schemas import MentorChatIn, MentorChatOut, MentorRecommendation
from backend import crud
from backend.ollama_client import ollama_chat_json

router = APIRouter(prefix="/mentor", tags=["mentor"])


@router.post("/chat", response_model=MentorChatOut)
async def mentor_chat(
    payload: MentorChatIn,
    user=Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    # 1) Pull the user's learning context from DB
    history = await crud.get_user_problem_history(db, user["id"], limit=30)
    stats = await crud.get_user_topic_stats(db, user["id"])

    # Make a compact context string for the model
    history_lines = []
    for h in history:
        topics = [t.strip() for t in (h.get("topics") or "").split(",") if t.strip()]
        history_lines.append(f"- {h['slug']} ({h['difficulty']}) status={h['status']} topics={topics}")

    system = (
        "You are an AI LeetCode mentor. Be practical and concise. "
        "Recommend problems based on the user's history and weaknesses. "
        "Return ONLY JSON with keys: reply, recommendations, next_steps. "
        "recommendations must be a list of {slug, title, difficulty, why}. "
        "Use real LeetCode slugs (e.g., 'number-of-islands')."
    )

    user_prompt = f"""
User message: {payload.message}
Weak topics (self-reported): {payload.weak_topics}
Target difficulty: {payload.target_difficulty}
Return up to {payload.limit} recommendations.

User topic stats:
- solved counts by topic: {stats.get("solved", {})}
- attempted counts by topic: {stats.get("attempted", {})}

Recent history (most recent first):
{chr(10).join(history_lines) if history_lines else "(no history yet)"}

Rules:
- Prefer problems that strengthen weak topics and core patterns.
- Avoid recommending problems that appear as solved in history.
- If no target difficulty is given, pick a good progression (mostly Medium, some Easy if fundamentals missing).
- Output JSON only.

Return JSON exactly like:
{{
  "reply": "...",
  "recommendations": [
    {{"slug":"...","title":"...","difficulty":"Easy|Medium|Hard","why":"..."}}
  ],
  "next_steps": ["...", "..."]
}}
"""

    try:
        obj = await ollama_chat_json(system=system, user=user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

    # 2) Normalize keys
    reply = obj.get("reply", "")
    recs = obj.get("recommendations", []) or []
    steps = obj.get("next_steps") or obj.get("nextSteps") or []

    # 3) Clean + store recommended problems into DB (so you can track them)
    cleaned = []
    seen = set()

    # Build a set of solved slugs so we don't store/recommend duplicates
    solved_slugs = {h["slug"] for h in history if h.get("status") == "solved"}

    for r in recs:
        slug = (r.get("slug") or "").strip()
        title = (r.get("title") or "").strip()
        difficulty = (r.get("difficulty") or "").strip()
        why = (r.get("why") or "").strip()

        if not slug or slug in seen or slug in solved_slugs:
            continue
        if difficulty not in {"Easy", "Medium", "Hard"}:
            # Default if model outputs something weird
            difficulty = payload.target_difficulty or "Medium"

        seen.add(slug)
        cleaned.append({"slug": slug, "title": title or slug, "difficulty": difficulty, "why": why or "Good next step."})

        # Save into problems table so you can track it later
        # topics unknown for AI-added problems -> store empty topics for now
        await crud.upsert_problem(db, slug, title or slug, difficulty, topics_csv="")

    return MentorChatOut(
        reply=reply,
        recommendations=[MentorRecommendation(**x) for x in cleaned[: payload.limit]],
        next_steps=steps,
    )
