from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from pathlib import Path
import subprocess
import uuid
import re
import os
import logging

# === Logging setup ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
RESUME_DIR = BASE_DIR / "resumes"
RESUME_DIR.mkdir(parents=True, exist_ok=True)

# === Jinja Environment ===
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False  # Disable escaping for LaTeX templates
)

def sanitize_filename(name: str) -> str:
    """Convert name to a safe filename format."""
    return re.sub(r'[^\w\-]+', '_', name.strip())

def generate_latex_resume(data) -> str:
    """
    Generate a LaTeX resume PDF and return filename.

    Args:
        data (dict or ResumeForm): Resume data
    Returns:
        str: PDF filename (relative to RESUME_DIR)
    Raises:
        RuntimeError: if LaTeX fails or file not generated
    """
    if hasattr(data, "dict"):
        data = data.dict()

    # Ensure all optional fields are present to avoid KeyErrors in template
    for field in ["github", "linkedin", "portfolio", "phone", "location"]:
        data.setdefault(field, "")

    file_id = uuid.uuid4().hex[:6]
    safe_name = sanitize_filename(data.get("name", "resume"))
    base_name = f"{safe_name}_{file_id}"
    tex_path = RESUME_DIR / f"{base_name}.tex"
    pdf_path = RESUME_DIR / f"{base_name}.pdf"

    try:
        logger.info("ðŸ”§ Rendering LaTeX template...")
        template = env.get_template("resume_template.tex")
        rendered_tex = template.render(**data)
        tex_path.write_text(rendered_tex, encoding="utf-8")

        logger.info(f"ðŸ“„ Compiling PDF: {pdf_path.name}")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(RESUME_DIR), str(tex_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not pdf_path.exists():
            logger.error("âŒ LaTeX compilation did not produce a PDF")
            raise RuntimeError("LaTeX compilation failed to produce a PDF file.")

        logger.info(f"âœ… PDF successfully created: {pdf_path.name}")
        return pdf_path.name

    except TemplateSyntaxError as e:
        logger.error(f"âŒ Template syntax error on line {e.lineno}: {e.message}")
        raise RuntimeError(f"Template error (line {e.lineno}): {e.message}")
    except subprocess.CalledProcessError:
        logger.error("âŒ pdflatex failed â€” ensure it's installed and available in PATH")
        raise RuntimeError("LaTeX compiler failed. Is `pdflatex` installed?")
    except Exception as e:
        logger.error(f"âŒ Resume generation failed: {e}")
        raise RuntimeError(f"Resume generation error: {e}")