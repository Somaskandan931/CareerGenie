from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger( __name__ )


class MatchRequest( BaseModel ) :
    resume_text: str


@router.post( "/match" )  # This creates the endpoint /match-jobs/match
async def match_jobs ( request: MatchRequest ) :
    try :
        # Mock job matching logic
        mock_matched_jobs = [
            {
                "id" : 1,
                "title" : "Senior Software Engineer",
                "company" : "TechCorp Inc.",
                "location" : "San Francisco, CA",
                "salary" : "$120,000 - $160,000",
                "type" : "Full-time",
                "description" : "We're looking for a senior software engineer.",
                "requirements" : ["Python", "SQL", "AWS", "Docker"],
                "fit_score" : 85,
                "matched_requirements" : ["Python", "SQL"]
            }
        ]

        return {"matched_jobs" : mock_matched_jobs}

    except Exception as e :
        logger.error( f"Job matching error: {str( e )}" )
        raise HTTPException( status_code=500, detail="Job matching failed" )