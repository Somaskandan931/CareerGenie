from pdfminer.high_level import extract_text
from docx import Document
import re

def extract_from_pdf(file_path: str) -> str:
    return extract_text(file_path)

def extract_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_resume_text(text: str) -> dict:
    # Very basic regex parsers (you can improve this)
    email = re.search(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.search(r"\+?\d[\d\s\-]{7,}", text)
    skills = re.findall(r"\b(?:Python|Java|SQL|React|Node|C\+\+|Machine Learning|AI)\b", text, re.I)

    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "skills": list(set([s.lower() for s in skills])),
        "raw_text": text[:1000]  # Optional preview
    }