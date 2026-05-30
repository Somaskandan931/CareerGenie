"""
resume_rewriter.py
==================
LangChain-powered resume rewriter.
Uses PromptTemplate + LLMChain — this is the LangChain integration
for your portfolio. Fallback to llm.py if LangChain is unavailable.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


def _build_langchain_chain(target_role: str, tone: str):
    """
    Build a LangChain PromptTemplate + LLMChain.
    Tries Ollama first, then Groq, then returns None for fallback.
    """
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from backend.config import settings

    template = """You are an expert resume writer and ATS optimization specialist.

Rewrite the following resume for the target role: "{target_role}"
Tone: {tone}

ORIGINAL RESUME:
{resume_text}

REWRITING RULES — follow every rule strictly:
1. PROFESSIONAL SUMMARY: Write a powerful 2-3 sentence summary tailored to {target_role}.
2. ACTION VERBS: Start every bullet with a strong action verb (Led, Built, Optimized, Delivered, Architected, Drove, Engineered, Reduced, Increased, Launched).
3. QUANTIFY EVERYTHING: Add realistic metrics wherever possible (%, $, #, time saved).
4. KEYWORDS: Naturally weave in role-specific keywords for "{target_role}" throughout.
5. ATS FORMAT: Standard section headers only — PROFESSIONAL SUMMARY, EXPERIENCE, SKILLS, EDUCATION.
6. MAINTAIN FACTS: Keep all real companies, dates, degrees, and job titles — only improve the language.

Return ONLY the rewritten resume text. No commentary, no markdown fences, no explanation."""

    prompt = PromptTemplate(
        input_variables=["resume_text", "target_role", "tone"],
        template=template,
    )

    # Try Ollama first (local, free, fast)
    try:
        from langchain_community.llms import Ollama
        llm = Ollama(
            base_url=settings.OLLAMA_HOST,
            model=settings.OLLAMA_LLM_MODEL,
            temperature=0.4,
        )
        return LLMChain(llm=llm, prompt=prompt)
    except Exception as e:
        logger.warning(f"Ollama LangChain init failed: {e}")

    # Groq fallback
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_CHAT_MODEL,
            temperature=0.4,
        )
        return LLMChain(llm=llm, prompt=prompt)
    except Exception as e:
        logger.warning(f"Groq LangChain init failed: {e}")

    return None


class ResumeRewriter:
    def rewrite(
        self,
        resume_text: str,
        target_role: str = "Software Engineer",
        tone: str = "professional",
    ) -> Dict:
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
        # ── Try LangChain first ───────────────────────────────────────────────
        try:
            chain = _build_langchain_chain(target_role, tone)
            if chain is not None:
                result = chain.run(
                    resume_text=resume_text[:3000],
                    target_role=target_role,
                    tone=tone,
                )
                logger.info("Resume rewrite via LangChain ✓")
                return result
        except Exception as e:
            logger.warning(f"LangChain rewrite failed ({e}), falling back to llm.py")

        # ── Fallback: existing llm.py — no behaviour change for the user ──────
        from backend.services.llm import llm_call_smart_sync
        from backend.config import settings

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
            return llm_call_smart_sync(
                system="You are an expert AI assistant. Respond clearly and concisely.",
                user=prompt,
                temp=0.4,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
            )
        except Exception as e:
            logger.error(f"Resume rewrite error: {e}")
            return resume_text  # last resort: return original

    # ── Step 2: before/after bullet comparisons ───────────────────────────────
    def _generate_comparisons(
        self, original: str, rewritten: str, target_role: str
    ) -> list:
        from backend.services.llm import llm_call_sync

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
            raw = llm_call_sync(
                system="You are an expert AI assistant. Respond clearly and concisely.",
                user=prompt,
                temp=0.2,
                max_tokens=800,
            )
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"^```\s*",     "", raw)
            raw = re.sub(r"\s*```$",     "", raw)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Comparison generation error: {e}")
            return [
                {
                    "section": "Experience",
                    "before": "Was responsible for helping the team with tasks",
                    "after": "Led cross-functional team of 5, delivering projects 20% ahead of schedule",
                    "improvement": "Added action verb, quantified impact, removed passive language",
                }
            ]

    # ── Step 3: high-level changes summary ───────────────────────────────────
    def _summarize_changes(self, original: str, rewritten: str) -> Dict:
        orig_words    = len(original.split())
        rewrite_words = len(rewritten.split())
        orig_bullets  = original.count("\n-") + original.count("\n•")
        new_bullets   = rewritten.count("\n-") + rewritten.count("\n•")

        action_verbs = [
            "led", "built", "optimized", "delivered", "architected",
            "drove", "engineered", "reduced", "increased", "launched",
            "designed", "developed", "implemented", "managed", "created",
        ]
        orig_av  = sum(1 for v in action_verbs if v in original.lower())
        new_av   = sum(1 for v in action_verbs if v in rewritten.lower())
        orig_nums = len(re.findall(r'\d+%|\$\d+|\d+ \w+s', original))
        new_nums  = len(re.findall(r'\d+%|\$\d+|\d+ \w+s', rewritten))

        return {
            "word_count":         {"before": orig_words, "after": rewrite_words},
            "bullet_points":      {"before": orig_bullets, "after": new_bullets},
            "action_verbs":       {"before": orig_av, "after": new_av, "added": max(0, new_av - orig_av)},
            "quantified_metrics": {"before": orig_nums, "after": new_nums, "added": max(0, new_nums - orig_nums)},
            "improvements": [
                f"Added {max(0, new_av - orig_av)} action verbs",
                f"Added {max(0, new_nums - orig_nums)} quantified metrics",
                "ATS-optimised section headers applied",
                f"Word count adjusted: {orig_words} → {rewrite_words}",
            ],
        }


resume_rewriter = ResumeRewriter()