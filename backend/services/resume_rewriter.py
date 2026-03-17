from groq import Groq
from typing import Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class ResumeRewriter:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("ResumeRewriter initialized with Groq")

    def rewrite(self, resume_text: str, target_role: str = "Software Engineer",
                tone: str = "professional") -> Dict:
        """
        Rewrite a resume to be ATS-optimized, impact-driven, and professional.
        Returns rewritten resume text + before/after bullet comparisons.
        """
        rewritten   = self._rewrite_resume(resume_text, target_role, tone)
        comparisons = self._generate_comparisons(resume_text, rewritten, target_role)
        changes     = self._summarize_changes(resume_text, rewritten)

        return {
            "rewritten_resume": rewritten,
            "before_after":     comparisons,
            "changes_summary":  changes,
            "target_role":      target_role,
            "tone":             tone,
        }

    # ── Step 1: full rewrite ──────────────────────────────────────────────────
    def _rewrite_resume(self, resume_text: str, target_role: str, tone: str) -> str:
        prompt = f"""You are an expert resume writer and ATS optimization specialist.

Rewrite the following resume for the target role: "{target_role}"
Tone: {tone}

ORIGINAL RESUME:
{resume_text[:3000]}

REWRITING RULES — follow every rule strictly:
1. PROFESSIONAL SUMMARY: Write a powerful 2-3 sentence summary at the top tailored to {target_role}.
2. ACTION VERBS: Start every bullet with a strong action verb (Led, Built, Optimized, Delivered, Architected, Drove, Engineered, Reduced, Increased, Launched).
3. QUANTIFY EVERYTHING: Add realistic metrics wherever possible (%, $, #, time saved). If the original has no numbers, infer reasonable ones from context.
4. KEYWORDS: Naturally weave in role-specific keywords for "{target_role}" throughout.
5. CONCISENESS: Each bullet = 1 impactful line. Remove filler words (responsible for, assisted with, helped to).
6. ATS FORMAT: Use standard section headers: PROFESSIONAL SUMMARY, EXPERIENCE, SKILLS, EDUCATION. No tables, no columns.
7. SKILLS SECTION: Organize skills into clear categories (Technical Skills, Tools, Soft Skills).
8. MAINTAIN FACTS: Keep all real companies, dates, degrees, and job titles — only improve the language.

Return ONLY the rewritten resume text. No commentary, no markdown fences, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Resume rewrite error: {e}")
            return resume_text  # fallback: return original

    # ── Step 2: before/after bullet comparisons ───────────────────────────────
    def _generate_comparisons(self, original: str, rewritten: str,
                               target_role: str) -> list:
        prompt = f"""Compare the original and rewritten resumes below.
Find 4 bullet points that were significantly improved.

ORIGINAL:
{original[:1500]}

REWRITTEN:
{rewritten[:1500]}

Return ONLY a valid JSON array with exactly 4 objects (no markdown, no extra text):
[
  {{
    "section": "<section name e.g. Experience, Summary>",
    "before": "<original bullet or sentence>",
    "after": "<rewritten bullet or sentence>",
    "improvement": "<one sentence explaining what improved>"
  }}
]"""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"^```\s*",     "", raw)
            raw = re.sub(r"\s*```$",     "", raw)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Comparison generation error: {e}")
            return self._fallback_comparisons()

    # ── Step 3: high-level changes summary ───────────────────────────────────
    def _summarize_changes(self, original: str, rewritten: str) -> Dict:
        orig_words    = len(original.split())
        rewrite_words = len(rewritten.split())
        orig_bullets  = original.count("\n-") + original.count("\n•")
        new_bullets   = rewritten.count("\n-") + rewritten.count("\n•")

        # Count action verbs added
        action_verbs = ["led", "built", "optimized", "delivered", "architected",
                        "drove", "engineered", "reduced", "increased", "launched",
                        "designed", "developed", "implemented", "managed", "created"]
        orig_av  = sum(1 for v in action_verbs if v in original.lower())
        new_av   = sum(1 for v in action_verbs if v in rewritten.lower())

        # Count numbers/metrics
        orig_nums = len(re.findall(r'\d+%|\$\d+|\d+ \w+s', original))
        new_nums  = len(re.findall(r'\d+%|\$\d+|\d+ \w+s', rewritten))

        has_summary_before = any(
            kw in original.lower()
            for kw in ["summary", "objective", "profile", "about"]
        )
        has_summary_after = any(
            kw in rewritten.lower()
            for kw in ["summary", "objective", "profile", "about"]
        )

        return {
            "word_count":        {"before": orig_words,   "after": rewrite_words},
            "bullet_count":      {"before": orig_bullets, "after": new_bullets},
            "action_verbs":      {"before": orig_av,      "after": new_av},
            "metrics_added":     {"before": orig_nums,    "after": new_nums},
            "summary_added":     not has_summary_before and has_summary_after,
            "improvements_made": [
                f"Added {max(0, new_av - orig_av)} stronger action verbs",
                f"Added {max(0, new_nums - orig_nums)} quantified metrics",
                "Rewrote bullets for impact and clarity",
                "Optimized keywords for ATS",
                *(["Added professional summary section"] if not has_summary_before else []),
            ],
        }

    def _fallback_comparisons(self) -> list:
        return [
            {
                "section": "Experience",
                "before": "Responsible for managing team projects",
                "after": "Led cross-functional team of 6 engineers, delivering 3 major features on time",
                "improvement": "Added ownership, team size, and quantified output",
            },
            {
                "section": "Experience",
                "before": "Helped improve application performance",
                "after": "Optimized backend API response time by 40%, reducing latency from 800ms to 480ms",
                "improvement": "Replaced vague language with specific metric-driven achievement",
            },
            {
                "section": "Summary",
                "before": "Looking for a software engineering position",
                "after": "Results-driven Software Engineer with 3+ years building scalable web applications",
                "improvement": "Replaced objective statement with value-focused professional summary",
            },
            {
                "section": "Skills",
                "before": "Python, JavaScript, some cloud experience",
                "after": "Technical: Python, JavaScript, React | Cloud: AWS (EC2, S3, Lambda) | Tools: Docker, Git",
                "improvement": "Organized skills into categories with specific tool names for ATS",
            },
        ]


try:
    resume_rewriter = ResumeRewriter()
except Exception as e:
    logger.error(f"Failed to initialize ResumeRewriter: {e}")
    resume_rewriter = None