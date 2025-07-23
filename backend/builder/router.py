from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import base64

router = APIRouter()
logger = logging.getLogger( __name__ )


class PersonalInfo( BaseModel ) :
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


class ResumeData( BaseModel ) :
    personal_info: PersonalInfo
    education: List[dict] = []
    experience: List[dict] = []
    skills: List[str] = []
    projects: List[dict] = []


@router.post( "/build-resume" )
async def build_resume ( resume_data: ResumeData ) :
    try :
        # Mock PDF generation - replace with actual PDF generation
        mock_pdf_content = b"Mock PDF content"
        pdf_base64 = base64.b64encode( mock_pdf_content ).decode( 'utf-8' )

        return {
            "pdf_base64" : pdf_base64,
            "message" : "Resume generated successfully"
        }

    except Exception as e :
        logger.error( f"Resume building error: {str( e )}" )
        raise HTTPException( status_code=500, detail="Resume generation failed" )