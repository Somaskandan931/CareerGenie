from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import subprocess
import uuid
import os

# === Paths ===
TEMPLATE_DIR = Path("C:/Users/somas/PycharmProjects/CareerGenie/backend/templates")
RESUME_DIR = Path("C:/Users/somas/PycharmProjects/CareerGenie/backend/resumes")
RESUME_DIR.mkdir(exist_ok=True)

# === Jinja Environment ===
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

def generate_latex_resume(data: dict) -> str:
    file_id = uuid.uuid4().hex[:6]
    base_name = f"{data['name'].replace(' ', '_')}_{file_id}"
    tex_path = RESUME_DIR / f"{base_name}.tex"
    pdf_path = RESUME_DIR / f"{base_name}.pdf"

    try:
        # Render LaTeX using Jinja2
        template = env.get_template("resume_template.tex")
        rendered_tex = template.render(**data)

        # Write .tex file
        tex_path.write_text(rendered_tex, encoding="utf-8")

        # Compile LaTeX to PDF
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(RESUME_DIR), str(tex_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not pdf_path.exists():
            raise RuntimeError("LaTeX compilation did not produce a PDF")

        return pdf_path.name

    except subprocess.CalledProcessError:
        raise RuntimeError("❌ LaTeX compilation failed. Is pdflatex installed?")
    except Exception as e:
        raise RuntimeError(f"❌ Resume generation error: {e}")
