"""
Resume API Routes
=================
Endpoints for resume upload, parsing, analysis, and rewriting.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from pydantic import BaseModel, Field

from backend.core.logging import get_logger
from backend.services.resume_parser import resume_parser
from backend.services.ats_scorer import ats_scorer
from backend.services.resume_rewriter import resume_rewriter

logger = get_logger("routes.resume")

router = APIRouter(prefix="/resume", tags=["Resume"])


# ── Request/Response Models ─────────────────────────────────────────────────────

class ResumeParseResponse(BaseModel):
    success: bool
    resume_text: str
    word_count: int
    confidence: dict = {}


class ATSRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    job_description: Optional[str] = None


class ATSResponse(BaseModel):
    result: dict
    _confidence: dict = {}


class ResumeRewriteRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    tone: str = "professional"


class ResumeRewriteResponse(BaseModel):
    result: dict


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    job_description: Optional[str] = None
    company_type: Optional[str] = None
    focus_area: Optional[str] = None


class ResumeAnalyzeResponse(BaseModel):
    ats_result: Optional[dict] = None
    ats_error: Optional[str] = None
    hr_panel: Optional[dict] = None
    hr_error: Optional[str] = None


# ── File Upload Validation ──────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE_MB = 10


def _validate_upload(file: UploadFile) -> None:
    """Validate uploaded file meets security requirements."""
    # Check extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if "." not in file.filename:
        raise HTTPException(
            status_code=400,
            detail=f"No file extension found. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse uploaded resume file (PDF or DOCX).
    
    Returns extracted text and basic metrics.
    """
    _validate_upload(file)
    
    try:
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Save to temp file for parsing
        import tempfile
        import uuid
        from pathlib import Path
        
        temp_dir = tempfile.gettempdir()
        # Use the already-validated file extension (guaranteed to have dot from _validate_upload)
        ext = "." + file.filename.rsplit(".", 1)[-1].lower()
        temp_path = Path(temp_dir) / f"resume_{uuid.uuid4().hex[:8]}{ext}"
        temp_path.write_bytes(content)


        
        try:
            result = resume_parser.parse(str(temp_path))
            return ResumeParseResponse(
                success=True,
                resume_text=result["resume_text"],
                word_count=result["word_count"],
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume parse error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ats/score", response_model=ATSResponse)
async def score_resume(request: ATSRequest):
    """
    Score resume against target role or job description.
    
    Provides ATS compatibility analysis and improvement suggestions.
    """
    try:
        result = ats_scorer.score_resume(
            request.resume_text,
            request.target_role,
            request.job_description
        )
        return ATSResponse(result=result)
    except Exception as e:
        logger.error(f"ATS score error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite", response_model=ResumeRewriteResponse)
async def rewrite_resume(request: ResumeRewriteRequest):
    """
    Rewrite resume for a specific target role and tone.
    
    Improves language, highlights relevant skills, and optimizes for ATS.
    """
    try:
        result = resume_rewriter.rewrite(
            request.resume_text,
            request.target_role,
            request.tone
        )
        return ResumeRewriteResponse(result=result)
    except Exception as e:
        logger.error(f"Resume rewrite error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Comprehensive resume analysis including ATS score and HR panel evaluation.
    
    Combines multiple analysis methods for a complete assessment.
    """
    ats_result = ats_error = hr_panel = hr_error = None
    
    try:
        from backend.services.ats_scorer import get_ats_scorer
        scorer = get_ats_scorer()
        ats_result = scorer.score(
            resume_text=request.resume_text,
            target_role=request.target_role,
            job_description=request.job_description or "",
        )
    except Exception as e:
        ats_error = str(e)
        logger.error(f"ATS scoring error: {e}", exc_info=True)
    
    try:
        hr_panel = _generate_hr_panel(
            resume_text=request.resume_text,
            target_role=request.target_role,
            company_type=request.company_type,
            focus_area=request.focus_area,
            num_questions=8,
        )
    except Exception as e:
        hr_error = str(e)
        logger.error(f"HR panel generation error: {e}", exc_info=True)
    
    return ResumeAnalyzeResponse(
        ats_result=ats_result,
        ats_error=ats_error,
        hr_panel=hr_panel,
        hr_error=hr_error,
    )


# ── HR Panel Generator (moved from main.py) ─────────────────────────────────────

def _generate_hr_panel(
    resume_text: str,
    target_role: str,
    company_type: Optional[str] = None,
    focus_area: Optional[str] = None,
    num_questions: int = 8,
) -> dict:
    """Generate HR-style evaluation of a resume."""
    import json
    import re
    from backend.services.llm import llm_call_sync
    
    company_ctx = company_type or "mid-size"
    focus_ctx = focus_area or "general"
    
    prompt = f"""You are a senior HR recruiter at a {company_ctx} tech company doing a {focus_ctx} evaluation.
Analyse the resume below for the role of "{target_role}" and return ONLY a single valid JSON object.

CRITICAL JSON RULES:
- Double quotes for ALL strings
- No trailing commas
- Escape any double quotes inside string values with backslash
- All text on single lines (no newlines inside string values)

RESUME:
{resume_text[:4000]}

Return EXACTLY this structure (fill in real values — do NOT keep placeholders):
{{
  "hire_verdict": "Yes",
  "verdict_summary": "one sentence summary of hiring decision",
  "verdict_confidence": 72,
  "dimension_scores": {{
    "technical_fit": 7,
    "experience_relevance": 6,
    "culture_fit": 7,
    "growth_potential": 8,
    "communication_clarity": 7
  }},
  "green_flags": ["strength 1", "strength 2", "strength 3"],
  "red_flags": ["concern 1", "concern 2"],
  "questions_to_ask": [
    {{"question": "Tell me about a challenging project.", "type": "behavioural", "reason": "Assesses problem-solving."}},
    {{"question": "How do you stay current with {target_role} trends?", "type": "technical", "reason": "Checks continuous learning."}}
  ],
  "salary_bracket_inr": "12-18 LPA",
  "suggested_interview_rounds": ["HR Screening", "Technical Round", "Manager Round"],
  "recruiter_notes": "Internal candid note about this candidate."
}}

hire_verdict must be one of: "Strong Yes", "Yes", "Maybe", "No", "Strong No"
questions_to_ask must have exactly {num_questions} items, type must be one of: technical, behavioural, situational
"""
    
    try:
        raw = llm_call_sync(
            system="You are an expert HR recruiter AI. Respond with ONLY valid JSON. No markdown, no extra text.",
            user=prompt,
            temp=0.3,
            max_tokens=2000,
        )
    except Exception as e:
        logger.error(f"HR panel LLM call failed: {e}", exc_info=True)
        return _hr_panel_fallback(target_role, company_type)
    
    # Clean up response
    raw = re.sub(r'```json\s*', '', raw or '')
    raw = re.sub(r'```\s*', '', raw)
    start = raw.find('{')
    end = raw.rfind('}')
    if start >= 0 and end > start:
        raw = raw[start:end + 1]
    else:
        return _hr_panel_fallback(target_role, company_type)
    
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)
    
    result = None
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        try:
            raw += '}' * (raw.count('{') - raw.count('}'))
            result = json.loads(raw)
        except Exception:
            pass
    
    if not isinstance(result, dict):
        return _hr_panel_fallback(target_role, company_type)
    
    # Validate and fix result
    valid_verdicts = {"Strong Yes", "Yes", "Maybe", "No", "Strong No"}
    if result.get("hire_verdict") not in valid_verdicts:
        result["hire_verdict"] = "Maybe"
    
    result.setdefault("verdict_summary", "Resume reviewed by AI recruiter.")
    result.setdefault("verdict_confidence", 60)
    result.setdefault("dimension_scores", {
        "technical_fit": 5, "experience_relevance": 5,
        "culture_fit": 5, "growth_potential": 5, "communication_clarity": 5,
    })
    result.setdefault("green_flags", [])
    result.setdefault("red_flags", [])
    result.setdefault("questions_to_ask", [])
    result.setdefault("salary_bracket_inr", "Market rate")
    result.setdefault("suggested_interview_rounds", ["HR Screening", "Technical Round"])
    result.setdefault("recruiter_notes", "Candidate requires further evaluation.")
    
    try:
        result["verdict_confidence"] = max(0, min(100, int(result["verdict_confidence"])))
    except (ValueError, TypeError):
        result["verdict_confidence"] = 60
    
    for k, v in result.get("dimension_scores", {}).items():
        try:
            result["dimension_scores"][k] = max(0, min(10, int(v)))
        except (ValueError, TypeError):
            result["dimension_scores"][k] = 5
    
    valid_types = {"technical", "behavioural", "situational"}
    result["questions_to_ask"] = [
        {
            "question": str(q.get("question", "")),
            "type": q.get("type", "behavioural") if q.get("type") in valid_types else "behavioural",
            "reason": str(q.get("reason", "")),
        }
        for q in result.get("questions_to_ask", [])
        if isinstance(q, dict) and q.get("question")
    ]
    
    return result


def _hr_panel_fallback(target_role: str, company_type: Optional[str]) -> dict:
    """Fallback HR panel when LLM fails."""
    return {
        "hire_verdict": "Maybe",
        "verdict_summary": f"Could not fully evaluate candidate for {target_role}. Manual review recommended.",
        "verdict_confidence": 50,
        "dimension_scores": {
            "technical_fit": 5, "experience_relevance": 5,
            "culture_fit": 5, "growth_potential": 5, "communication_clarity": 5,
        },
        "green_flags": ["Resume submitted for review"],
        "red_flags": ["Automated analysis incomplete — please review manually"],
        "questions_to_ask": [
            {"question": f"Walk me through your most relevant experience for this {target_role} role.", "type": "behavioural", "reason": "Establishes baseline fit."},
            {"question": "What motivated you to apply for this position?", "type": "behavioural", "reason": "Gauges genuine interest."},
            {"question": "Describe a challenging problem you solved recently.", "type": "situational", "reason": "Assesses problem-solving ability."},
        ],
        "salary_bracket_inr": "Market rate",
        "suggested_interview_rounds": ["HR Screening", "Technical Round", "Manager Round"],
        "recruiter_notes": "Automated HR panel generation encountered an error. Manual screening advised.",
    }