from fastapi import APIRouter, UploadFile, File
import shutil
import uuid
import tempfile
import os

from .extractors import extract_resume

router = APIRouter(prefix="/upload-resume", tags=["Resume Parsing"])


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        parsed = extract_resume(temp_path)
    finally:
        os.remove(temp_path)

    return {
        "status": "success",
        "resume_text": parsed["resume_text"],
        "word_count": parsed["length"]
    }
