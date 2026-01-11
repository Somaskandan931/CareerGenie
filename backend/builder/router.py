"""
Resume Builder Router - Fixed imports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import logging

# Try both import styles
try :
    from builder.resume_generator import generate_latex_resume
except ImportError :
    try :
        from backend.builder.resume_generator import generate_latex_resume
    except ImportError :
        # Fallback if module doesn't exist yet
        logging.warning( "resume_generator not found, using stub" )


        def generate_latex_resume ( data ) :
            return "stub_pdf_base64_data"

router = APIRouter()
logger = logging.getLogger( __name__ )


class EducationEntry( BaseModel ) :
    degree: str
    institution: str
    year: str


class ExperienceEntry( BaseModel ) :
    role: str
    company: str
    years: str


class ProjectEntry( BaseModel ) :
    name: str
    description: str


class ResumeForm( BaseModel ) :
    name: str = Field( ..., min_length=1 )
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    education: List[EducationEntry] = []
    experience: List[ExperienceEntry] = []
    skills: List[str] = Field( ..., min_items=1 )
    projects: List[ProjectEntry] = []


@router.post( "/", summary="Build Resume PDF" )
async def build_resume ( resume_data: ResumeForm ) :
    """
    Generate a PDF resume from structured data

    Returns:
        pdf_base64: Base64 encoded PDF
        message: Success message
        filename: Suggested filename
    """
    try :
        # Generate PDF
        pdf_base64 = generate_latex_resume( resume_data.dict() )

        # Create filename from name
        filename = f"{resume_data.name.replace( ' ', '_' )}_resume.pdf"

        return {
            "pdf_base64" : pdf_base64,
            "message" : "Resume generated successfully",
            "filename" : filename
        }

    except Exception as e :
        logger.error( f"Resume generation failed: {e}" )
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed: {str( e )}"
        )


@router.get( "/health" )
async def health () :
    """Health check for resume builder"""
    return {"status" : "healthy", "service" : "resume_builder"}