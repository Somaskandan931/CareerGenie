from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import subprocess
import uuid
import os

router = APIRouter()

TEMPLATE_DIR = Path("templates")
RESUME_DIR = Path("resumes")
RESUME_DIR.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

class ResumeForm(BaseModel):
    name: str
    email: str
    phone: str
    education: str
    experience: str
    skills: list[str]

@router.post("/generate-latex")
def generate_latex_resume(data: ResumeForm):
    file_id = uuid.uuid4().hex[:6]
    base_name = f"{data.name.replace(' ', '_')}_{file_id}"
    tex_file = RESUME_DIR / f"{base_name}.tex"
    pdf_file = RESUME_DIR / f"{base_name}.pdf"

    try:
        template = env.get_template("resume_template.tex")
        rendered_tex = template.render(**data.dict())
        tex_file.write_text(rendered_tex, encoding="utf-8")

        subprocess.run([
            "pdflatex", "-interaction=nonstopmode",
            "-output-directory", str(RESUME_DIR), str(tex_file)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if pdf_file.exists():
            return {
                "message": "PDF generated successfully",
                "pdf_file": pdf_file.name,
                "download_link": f"/builder/download/{pdf_file.name}"
            }
        return JSONResponse(status_code=500, content={"error": "PDF generation failed"})

    except subprocess.CalledProcessError:
        return JSONResponse(status_code=500, content={"error": "LaTeX compilation failed"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/download/{file_name}")
def download_resume(file_name: str):
    file_path = RESUME_DIR / file_name
    if file_path.exists():
        return FileResponse(path=file_path, filename=file_name, media_type="application/pdf")
    return JSONResponse(status_code=404, content={"error": "File not found"})
