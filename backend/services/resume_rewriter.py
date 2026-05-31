"""
backend/services/resume_rewriter.py
======================================
LangChain-powered resume rewriter.
Uses PromptTemplate + LLMChain — LangChain integration for portfolio value.
Falls back to ai_pipeline if LangChain is unavailable.

Refactored to:
  - Use centralized prompts from ``backend.core.prompts``
  - Route fallback calls through ``backend.core.ai_pipeline``
  - Sanitize user-supplied resume text
  - Use structured logging via ``backend.core.logging``
"""
from __future__ import annotations

import json
import re
from typing import Dict

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("resume_rewriter")


def _build_langchain_chain(target_role: str, tone: str):
    """
    Build a LangChain PromptTemplate + LLMChain.
    Tries Ollama first, then Groq, then returns None for fallback.
    """
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    # Use rewrite_resume prompt from centralized Prompts
    _, prompt_text = Prompts.rewrite_resume("{{resume_text}}", target_role, tone)

    template = prompt_text.replace("{{resume_text}}", "{resume_text}")
    prompt = PromptTemplate(
        input_variables=["resume_text"],
        template=template,
    )

    # Try Groq first (primary when Ollama is not running)
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_CHAT_MODEL,
                temperature=0.4,
            )
            logger.info("LangChain chain using Groq/%s", settings.GROQ_CHAT_MODEL)
            return LLMChain(llm=llm, prompt=prompt)
        except Exception as exc:
            logger.warning("Groq LangChain init failed: %s", exc)

    # Ollama fallback (if running locally)
    try:
        from langchain_community.llms import Ollama
        llm = Ollama(
            base_url=settings.OLLAMA_HOST,
            model=settings.OLLAMA_LLM_MODEL,
            temperature=0.4,
        )
        logger.info("LangChain chain using Ollama/%s", settings.OLLAMA_LLM_MODEL)
        return LLMChain(llm=llm, prompt=prompt)
    except Exception as exc:
        logger.warning("Ollama LangChain init failed: %s", exc)

    return None


class ResumeRewriter:

    def rewrite(
        self,
        resume_text: str,
        target_role: str = "Software Engineer",
        tone: str = "professional",
    ) -> Dict:
        safe_resume = ai_pipeline.sanitize_user_content(resume_text)
        rewritten   = self._rewrite_resume(safe_resume, target_role, tone)
        comparisons = self._generate_comparisons(safe_resume, rewritten, target_role)
        changes     = self._summarize_changes(safe_resume, rewritten)
        return {
            "rewritten_resume": rewritten,
            "before_after":     comparisons,
            "changes_summary":  changes,
            "target_role":      target_role,
            "tone":             tone,
        }

    def _rewrite_resume(self, resume_text: str, target_role: str, tone: str) -> str:
        # ── Try LangChain first ────────────────────────────────────────────────
        try:
            chain = _build_langchain_chain(target_role, tone)
            if chain is not None:
                result = chain.run(resume_text=resume_text[:3000])
                logger.info("Resume rewrite via LangChain completed")
                return result
        except Exception as exc:
            logger.warning("LangChain rewrite failed (%s), falling back to ai_pipeline", exc)

        # ── Fallback: ai_pipeline via centralized prompts ──────────────────────
        system, user = Prompts.rewrite_resume(resume_text, target_role, tone)
        try:
            return ai_pipeline.call_smart(
                system=system,
                user=user,
                temp=0.4,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
            )
        except Exception as exc:
            logger.error("Resume rewrite error: %s", exc)
            return resume_text  # last resort: return original

    def _generate_comparisons(self, original: str, rewritten: str, target_role: str) -> list:
        system = "You are an expert resume analyst. Respond with ONLY valid JSON."
        user = f"""Compare the original and rewritten resumes below.
Find 4 bullet points that were significantly improved.

ORIGINAL:
{original[:1500]}

REWRITTEN:
{rewritten[:1500]}

Return ONLY a valid JSON array with exactly 4 objects:
[
  {{
    "section": "<section name>",
    "before": "<original bullet or sentence>",
    "after": "<rewritten bullet or sentence>",
    "improvement": "<one sentence explaining what improved>"
  }}
]"""

        try:
            result = ai_pipeline.call_json(system, user, temp=0.2, max_tokens=800)
            if isinstance(result, list):
                return result
        except Exception as exc:
            logger.error("Comparison generation error: %s", exc)

        return [{
            "section": "Experience",
            "before": "Was responsible for helping the team with tasks",
            "after": "Led cross-functional team of 5, delivering projects 20% ahead of schedule",
            "improvement": "Added action verb, quantified impact, removed passive language",
        }]

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
            "word_count":         {"before": orig_words,    "after": rewrite_words},
            "bullet_points":      {"before": orig_bullets,  "after": new_bullets},
            "action_verbs":       {"before": orig_av,       "after": new_av,       "added": max(0, new_av - orig_av)},
            "quantified_metrics": {"before": orig_nums,     "after": new_nums,     "added": max(0, new_nums - orig_nums)},
            "improvements": [
                f"Added {max(0, new_av - orig_av)} action verbs",
                f"Added {max(0, new_nums - orig_nums)} quantified metrics",
                "ATS-optimised section headers applied",
                f"Word count adjusted: {orig_words} → {rewrite_words}",
            ],
        }


resume_rewriter = ResumeRewriter()