from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, UserProblem
from mock_data import mock_problems

@router.post("/mock_sync/{user_id}")
def mock_sync(user_id: int, db: Session = Depends(get_db)):
    synced = []
    for p in mock_problems:
        # Add problem if it doesn't exist
        problem = db.query(Problem).filter_by(leetcode_id=p["leetcode_id"]).first()
        if not problem:
            problem = Problem(
                leetcode_id=p["leetcode_id"],
                title=p["title"],
                difficulty=p["difficulty"],
                topic=p["topic"]
            )
            db.add(problem)
            db.commit()
            db.refresh(problem)

        # Link to user with random status for demo
        import random
        status = random.choice(["solved", "attempted", "not_solved"])
        user_problem = UserProblem(
            user_id=user_id,
            problem_id=problem.id,
            status=status
        )
        db.add(user_problem)
        db.commit()
        synced.append({"title": problem.title, "status": status})

    return {"message": "Mock problems synced", "data": synced}
