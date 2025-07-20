from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
import tempfile
import docx2txt
import pdfplumber

router = APIRouter()

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX using docx2txt."""
    return docx2txt.process(file_path)

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        # Validate extension
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()

        if ext not in [".pdf", ".docx"]:
            return JSONResponse(status_code=400, content={"error": "Only .pdf and .docx files are supported."})

        # Save uploaded file to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Extract text
        if ext == ".pdf":
            extracted_text = extract_text_from_pdf(tmp_path)
        else:
            extracted_text = extract_text_from_docx(tmp_path)

        # Clean up temp file
        os.remove(tmp_path)

        # Truncate for preview (optional)
        preview_text = extracted_text.strip()[:3000]

        return {
            "filename": file.filename,
            "text_preview": preview_text,
            "char_count": len(extracted_text),
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Resume parsing failed: {str(e)}"})
