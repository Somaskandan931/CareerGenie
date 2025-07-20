from fastapi import APIRouter, Body
from backend.matcher.matcher import calculate_fit_score

router = APIRouter()

@router.post("/match-jobs")
def match_jobs(
    resume_text: str = Body(...),
    jobs: list = Body(...)
):
    try:
        scored_jobs = calculate_fit_score(resume_text, jobs)
        return {"matches": scored_jobs[:5]}  # Return top 5
    except Exception as e:
        return {"error": str(e)}
