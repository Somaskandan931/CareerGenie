import os
from typing import List, Dict
from anthropic import Anthropic
from .vector_store import semantic_search

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_skills(text: str) -> List[str]:
    skills = [
        "python", "java", "sql", "machine learning", "deep learning",
        "fastapi", "docker", "aws", "tensorflow", "pytorch", "nlp"
    ]
    text = text.lower()
    return [s for s in skills if s in text]


def generate_explanation(resume: str, job: Dict) -> str:
    prompt = f"""
You are an AI career assistant.

Resume:
{resume[:1500]}

Job Description:
{job['description'][:1500]}

Explain why this candidate matches the job.
Mention strengths and gaps clearly.
"""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def match_resume_to_jobs(resume_text: str, top_k: int) -> List[Dict]:
    retrieved_jobs = semantic_search(resume_text, top_k)
    resume_skills = set(extract_skills(resume_text))

    matches = []

    for job in retrieved_jobs:
        job_skills = set(extract_skills(job.get("description", "")))

        matched = list(resume_skills & job_skills)
        missing = list(job_skills - resume_skills)

        score = min(95, 55 + len(matched) * 8)

        explanation = generate_explanation(resume_text, job)

        matches.append({
            "title": job["title"],
            "company": job["company"],
            "match_score": round(score, 1),
            "matched_skills": matched,
            "missing_required_skills": missing,
            "explanation": explanation,
            "recommendation": "Strong Match" if score >= 75 else "Moderate Match",
            "apply_link": job["apply_link"]
        })

    return matches
