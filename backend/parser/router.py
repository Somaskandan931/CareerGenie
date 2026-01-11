"""
Resume Parser Router - Fixed imports
"""

import os
import tempfile
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import logging

# Try both import styles
try:
    from parser.extractors import extract_from_pdf, extract_from_docx, parse_resume_text
except ImportError:
    from backend.parser.extractors import extract_from_pdf, extract_from_docx, parse_resume_text

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
PREVIEW_LENGTH = 1000


@router.post("/", summary="Parse uploaded resume (PDF/DOCX)")
async def parse_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept a resume file upload (PDF or DOCX), extract text, and parse resume fields.

    Returns:
        parsed_data: Dict with parsed resume details (name, skills, experience, etc.)
        resume_text: First 1000 characters of raw extracted text
        filename: Original uploaded filename
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Supported: PDF, DOC, DOCX"
        )

    tmp_path = None
    try:
        # Save uploaded file to a temp file
        suffix = os.path.splitext(file.filename)[1] or ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
            logger.info(f"Saved upload to temporary file {tmp_path}")

        # Extract text based on file type
        if file.content_type == "application/pdf":
            resume_text = extract_from_pdf(tmp_path)
        else:
            resume_text = extract_from_docx(tmp_path)

        # Parse the extracted text
        parsed_data = parse_resume_text(resume_text)

        return {
            "parsed_data": parsed_data,
            "resume_text": resume_text[:PREVIEW_LENGTH],
            "filename": file.filename,
        }

    except Exception as e:
        logger.error(f"Resume parsing error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Resume parsing failed: {str(e)}"
        )

    finally:
        # Cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.info(f"Deleted temporary file {tmp_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp file {tmp_path}: {cleanup_err}")


@router.get("/health")
async def health():
    """Health check for resume parser"""
    return {"status": "healthy", "service": "resume_parser"}