"""
backend/core/prompts.py
========================
Centralized, versioned prompt library — **every** LLM prompt lives here.

No scattered prompt strings across services.  Each static method returns a
``(system_prompt, user_prompt)`` tuple ready for :func:`ai_pipeline.call`.

Rules enforced by this module:
  - Prompts that require JSON output include ``_STRICT_JSON`` in the system.
  - Resume text is always truncated here (never rely on the caller to do it).
  - Prompt strings are factored into shared constants to avoid drift.

Usage::

    from backend.core.prompts import Prompts
    from backend.core import ai_pipeline

    system, user = Prompts.ats_score(resume_text, target_role, jd)
    data = ai_pipeline.call_json(system, user)
"""
from __future__ import annotations

from typing import List, Optional, Tuple

__all__ = ["Prompts"]


# ── Shared constants ──────────────────────────────────────────────────────────

_STRICT_JSON = (
    "Respond with ONLY valid JSON. "
    "No markdown fences, no explanations, no extra text. "
    "Use double quotes for all strings. No trailing commas."
)

_CAREER_ADVISOR_ROLE = (
    "You are an expert career advisor specialising in the Indian tech job market "
    "with deep expertise in ML, software engineering, automotive, and manufacturing roles."
)

# Character limits — keep prompts within context windows
_RESUME_SHORT = 800
_RESUME_MEDIUM = 1200
_RESUME_LONG = 3000
_RESUME_FULL = 4000
_JD_MAX = 3000


# ── Prompt library ────────────────────────────────────────────────────────────

class Prompts:
    """
    Versioned, centralized prompt templates for Career Genie.

    Every ``@staticmethod`` returns ``Tuple[str, str]`` — ``(system, user)`` —
    unless it only produces a system string, in which case it returns ``str``.

    **Never** call ``llm_call_*`` directly inside these methods; they are pure
    string factories.  The actual LLM invocation always happens in the caller
    via ``ai_pipeline.call()`` or ``ai_pipeline.call_json()``.
    """

    # ── ATS Scoring ───────────────────────────────────────────────────────────

    @staticmethod
    def ats_score(
        resume_text: str,
        target_role: str,
        job_description: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Score a resume against a role / JD and return structured ATS feedback.

        Returns JSON with keys: overall_score, keyword_score, format_score,
        missing_keywords, found_keywords, section_feedback, bullet_quality,
        improvements, ats_verdict, verdict_reason.
        """
        system = f"You are an expert ATS analyzer. {_STRICT_JSON}"

        if job_description and job_description.strip():
            context = (
                f"JOB DESCRIPTION:\n{job_description[:_JD_MAX]}\n\n"
                f'TARGET ROLE: "{target_role}"'
            )
        else:
            context = f'TARGET ROLE: "{target_role}"'

        user = f"""{context}

RESUME:
{resume_text[:_RESUME_FULL]}

Return EXACTLY this JSON structure:
{{
  "overall_score": 75,
  "keyword_score": 70,
  "format_score": 80,
  "missing_keywords": ["skill1", "skill2"],
  "found_keywords": ["skill3", "skill4"],
  "section_feedback": {{
    "experience": "feedback here",
    "skills": "feedback here",
    "education": "feedback here",
    "summary": "feedback here",
    "formatting": "feedback here"
  }},
  "bullet_quality": {{
    "score": 70,
    "issues": ["issue1"],
    "good_examples": ["example1"]
  }},
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "ats_verdict": "Good",
  "verdict_reason": "reason here"
}}"""
        return system, user

    # ── Career Advice ─────────────────────────────────────────────────────────

    @staticmethod
    def career_advice(
        resume_text: str,
        target_role: str,
        current_role: Optional[str] = None,
        job_context: str = "",
        ats_context: str = "",
        market_context: str = "",
        profile_context: str = "",
    ) -> Tuple[str, str]:
        """
        Generate structured career advice synthesizing multiple context signals.

        Accepts optional context blocks (job matches, ATS result, market data,
        user behaviour) so the LLM can produce maximally relevant advice.
        """
        system = f"{_CAREER_ADVISOR_ROLE} Respond with structured advice."
        user = f"""Resume: {resume_text[:_RESUME_MEDIUM]}
Current Role: {current_role or "Entry-level"}
Target Role: {target_role}

Recent Job Matches:
{job_context or "None"}

ATS Analysis:
{ats_context or "Not available"}

Market Intelligence:
{market_context or "Not available"}

User Behaviour Signals:
{profile_context or "No signals yet"}

Provide structured career advice covering:
1. CURRENT ASSESSMENT: 2-3 sentences evaluating market readiness.
2. CRITICAL SKILL GAPS: Exactly 4 gaps, one per line in this format:
   - SkillName | Importance: Critical/Important | Current: None/Beginner | Target: Intermediate/Advanced
3. MARKET INSIGHTS: 2 sentences on demand and salary trends.
4. ACTION PLAN: 5 specific, actionable steps, each on its own line starting with a dash.

Be direct. Reference the data provided above — do not give generic advice."""
        return system, user

    # ── Roadmap Generation ────────────────────────────────────────────────────

    @staticmethod
    def generate_roadmap(
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        duration_weeks: int,
        resources_section: str = "",
    ) -> Tuple[str, str]:
        """
        Build a week-by-week learning roadmap structured into phases.

        Returns JSON — use ``ai_pipeline.call_json()`` or
        ``ai_pipeline.call_smart()`` (higher token budget recommended).
        """
        system = f"You are an expert career coach and curriculum designer. {_STRICT_JSON}"
        gaps_str = ", ".join(skill_gaps) if skill_gaps else "general software engineering skills"
        resources_block = (
            f"Reliable resources to incorporate:\n{resources_section}"
            if resources_section
            else ""
        )
        user = f"""Candidate wants to become: "{target_role}"
Resume excerpt: {resume_text[:_RESUME_SHORT]}
Skill gaps to address: {gaps_str}
Duration: {duration_weeks} weeks
{resources_block}

Return ONLY a valid JSON object (no markdown):
{{
  "title": "{duration_weeks}-Week Path to {target_role}",
  "target_role": "{target_role}",
  "duration_weeks": {duration_weeks},
  "total_hours_estimated": 120,
  "summary": "<2-3 sentence overview of the roadmap>",
  "phases": [
    {{
      "phase_number": 1,
      "phase_title": "<e.g. Foundations>",
      "weeks": "1-3",
      "focus": "<primary focus area>",
      "weekly_tasks": [
        {{
          "week": 1,
          "topic": "<topic name>",
          "description": "<what to study / build>",
          "resources": [
            {{
              "title": "<resource name>",
              "type": "course|docs|video|book",
              "url": "<url or null>",
              "duration": "<e.g. 4 hours>"
            }}
          ],
          "milestone": "<tangible achievement by end of week>",
          "hours_per_week": 8
        }}
      ]
    }}
  ],
  "final_milestone": "<capstone project / outcome>",
  "tips": ["<practical tip 1>", "<practical tip 2>", "<practical tip 3>"]
}}"""
        return system, user

    # ── Project Suggestions ───────────────────────────────────────────────────

    @staticmethod
    def suggest_projects(
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        difficulty: str = "intermediate",
        num_projects: int = 5,
    ) -> Tuple[str, str]:
        """
        Suggest portfolio projects that close specific skill gaps.

        Returns a JSON array of project objects.
        *difficulty* should be one of: ``"beginner"``, ``"intermediate"``,
        ``"advanced"``.
        """
        system = (
            "You are a software engineering mentor specializing in portfolio projects. "
            f"{_STRICT_JSON}"
        )
        gaps_str = ", ".join(skill_gaps) if skill_gaps else "Python, System Design, REST APIs"
        user = f"""Candidate targeting: "{target_role}"
Background: {resume_text[:_RESUME_SHORT]}
Skills to develop: {gaps_str}
Difficulty level: {difficulty}

Suggest {num_projects} hands-on portfolio projects. Return ONLY a valid JSON array:
[
  {{
    "id": "project_1",
    "title": "<catchy project title>",
    "tagline": "<one-sentence value proposition>",
    "difficulty": "{difficulty}",
    "estimated_weeks": 3,
    "hours_per_week": 10,
    "tech_stack": ["<tech1>", "<tech2>"],
    "skills_covered": ["<skill1>"],
    "skills_from_gaps": ["<gap skill covered>"],
    "description": "<2-3 sentences describing the project>",
    "key_features": ["<feature 1>", "<feature 2>", "<feature 3>"],
    "learning_outcomes": ["<concrete outcome 1>", "<concrete outcome 2>"],
    "impact_statement": "<why this impresses recruiters for {target_role}>",
    "github_template": null,
    "bonus_extensions": ["<stretch feature 1>"]
  }}
]"""
        return system, user

    # ── Interview Questions ───────────────────────────────────────────────────

    @staticmethod
    def interview_questions(
        role: str,
        interview_type: str,
        num_questions: int,
        resume_text: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate role-specific, difficulty-graded interview questions.

        *interview_type* should be one of: ``"technical"``, ``"behavioural"``,
        ``"situational"``, ``"hr"``, ``"system_design"``.
        Returns a JSON array.
        """
        system = f"You are an expert technical interviewer at a top tech company. {_STRICT_JSON}"
        context = (
            f"\nCandidate background: {resume_text[:600]}"
            if resume_text
            else ""
        )
        user = f"""Generate {num_questions} interview questions for a "{role}" position.
Interview type: {interview_type}{context}

Return ONLY a valid JSON array:
[
  {{
    "id": 1,
    "question": "<the interview question>",
    "type": "{interview_type}",
    "difficulty": "easy|medium|hard",
    "hints": "<1 sentence hint for the candidate>",
    "ideal_answer_points": ["key point 1", "key point 2", "key point 3"]
  }}
]"""
        return system, user

    # ── Answer Evaluation ─────────────────────────────────────────────────────

    @staticmethod
    def evaluate_answer(
        question: str,
        answer: str,
        role: str,
        interview_type: str,
    ) -> Tuple[str, str]:
        """
        Score a candidate's interview answer on a 0-10 scale.

        Returns JSON with: score, strengths, improvements,
        sample_better_answer, follow_up_question.
        """
        system = f"You are an expert interviewer evaluating candidates fairly. {_STRICT_JSON}"
        user = f"""Evaluate this interview answer for a "{role}" position ({interview_type} interview).

Question: {question}
Candidate's answer: {answer[:2000]}

Return ONLY valid JSON:
{{
  "score": 7,
  "strengths": ["<specific strength>", "<another strength>"],
  "improvements": ["<specific, actionable improvement>"],
  "sample_better_answer": "<concise model answer in 2-3 sentences>",
  "follow_up_question": "<a natural follow-up the interviewer would ask>"
}}"""
        return system, user

    # ── HR Recruiter Panel ────────────────────────────────────────────────────

    @staticmethod
    def hr_panel(
        resume_text: str,
        target_role: str,
        company_type: str = "mid-size",
        focus_area: str = "general",
        num_questions: int = 8,
    ) -> Tuple[str, str]:
        """
        Simulate an HR recruiter panel evaluation of a resume.

        *company_type*: ``"startup"``, ``"mid-size"``, ``"enterprise"``
        *focus_area*: ``"general"``, ``"technical"``, ``"culture"``, ``"leadership"``

        Returns rich JSON including hire verdict, dimension scores,
        red/green flags, and a list of interview questions.
        """
        system = f"You are a senior HR recruiter at a {company_type} tech company. {_STRICT_JSON}"
        user = f"""You are conducting a {focus_area} evaluation for the role: "{target_role}".

CANDIDATE RESUME:
{resume_text[:_RESUME_FULL]}

Return EXACTLY this JSON structure (replace placeholder values with real analysis):
{{
  "hire_verdict": "Yes",
  "verdict_summary": "<one sentence hiring decision rationale>",
  "verdict_confidence": 72,
  "dimension_scores": {{
    "technical_fit": 7,
    "experience_relevance": 6,
    "culture_fit": 7,
    "growth_potential": 8,
    "communication_clarity": 7
  }},
  "green_flags": ["<genuine strength>", "<another strength>"],
  "red_flags": ["<legitimate concern>"],
  "questions_to_ask": [
    {{
      "question": "<interview question>",
      "type": "behavioural",
      "reason": "<why this question is relevant for this candidate>"
    }}
  ],
  "salary_bracket_inr": "12-18 LPA",
  "suggested_interview_rounds": ["HR Screening", "Technical Round", "Manager Round"],
  "recruiter_notes": "<candid internal note a recruiter would write>"
}}

Constraints:
- hire_verdict must be one of: "Strong Yes", "Yes", "Maybe", "No", "Strong No"
- questions_to_ask must contain exactly {num_questions} items
- question type must be one of: technical | behavioural | situational"""
        return system, user

    # ── Resume Rewriter ───────────────────────────────────────────────────────

    @staticmethod
    def rewrite_resume(
        resume_text: str,
        target_role: str,
        tone: str = "professional",
    ) -> Tuple[str, str]:
        """
        Rewrite a resume optimized for ATS and human readability.

        *tone*: ``"professional"``, ``"assertive"``, ``"concise"``

        Returns plain rewritten resume text (no JSON).
        Use ``ai_pipeline.call_smart()`` for best results.
        """
        system = "You are an expert resume writer and ATS optimization specialist."
        user = f"""Rewrite the following resume for the target role: "{target_role}"
Tone: {tone}

ORIGINAL RESUME:
{resume_text[:_RESUME_LONG]}

REWRITING RULES:
1. PROFESSIONAL SUMMARY — Write a powerful 2-3 sentence summary tailored to "{target_role}".
2. ACTION VERBS — Start every bullet point with a strong, varied action verb.
3. QUANTIFY — Add realistic metrics wherever possible (%, ₹, count, time saved).
4. KEYWORDS — Naturally weave in role-specific keywords for "{target_role}".
5. ATS FORMAT — Use standard section headers: Summary, Experience, Skills, Education, Projects.
6. MAINTAIN FACTS — Keep all real companies, dates, degrees, and job titles unchanged.
7. STAR STRUCTURE — Frame achievement bullets as Situation→Task→Action→Result.

Return ONLY the rewritten resume text. No commentary, no markdown, no explanations."""
        return system, user

    # ── Market Analysis ───────────────────────────────────────────────────────

    @staticmethod
    def market_analysis(
        role: str,
        location: str,
        trend_summary: str,
        hot_skills: List[str],
    ) -> Tuple[str, str]:
        """
        Produce a 3-paragraph job market analysis with data-backed recommendations.

        *trend_summary* should be a pre-formatted string of Google Trends / SERP
        data passed by the market insights service.
        """
        system = (
            "You are a labour market analyst specialising in the Indian tech "
            "and manufacturing job market. Be specific, data-driven, and concise."
        )
        skills_str = ", ".join(hot_skills) if hot_skills else "None identified"
        user = f"""Role: {role}
Location context: {location}
Google Trends data (past 12 months, scale 0-100):
{trend_summary}
Hot / rising skills: {skills_str}

Write a 3-paragraph market analysis covering:
1. Current demand outlook for "{role}" in {location} — reference specific trend data.
2. Most in-demand skills and why they matter — reference trend data.
3. Salary expectations (in LPA) and 3-year career growth outlook.

End with exactly 3 bullet-point recommendations for job seekers targeting this role.
Be specific and cite the trend data you were given."""
        return system, user

    # ── Resume Intelligence ───────────────────────────────────────────────────

    @staticmethod
    def resume_intelligence(resume_text: str, target_role: str) -> Tuple[str, str]:
        """
        Deep resume analysis: STAR detection, weak verbs, quantification gaps.

        Returns JSON — part of the Resume Intelligence Layer (Phase 3).
        """
        system = f"You are an expert resume analyst and talent acquisition specialist. {_STRICT_JSON}"
        user = f"""Perform a deep intelligence analysis on this resume for the role: "{target_role}"

RESUME:
{resume_text[:_RESUME_FULL]}

Return ONLY this JSON:
{{
  "impact_score": 72,
  "quantification_rate": 0.4,
  "weak_verbs_found": ["helped", "worked on", "assisted"],
  "strong_verbs_used": ["engineered", "led", "reduced"],
  "star_bullets": ["<example of a well-structured bullet>"],
  "non_star_bullets": ["<bullet that needs STAR structure>"],
  "duplicate_bullets": ["<repeated theme or phrasing>"],
  "keyword_density": {{
    "high_frequency": ["python", "fastapi"],
    "missing_for_role": ["kubernetes", "ci/cd"]
  }},
  "recruiter_readability": 7,
  "recommendations": [
    "<specific, actionable improvement 1>",
    "<specific, actionable improvement 2>",
    "<specific, actionable improvement 3>"
  ]
}}"""
        return system, user

    # ── Job Coach Chat ────────────────────────────────────────────────────────

    @staticmethod
    def job_coach_system(resume_text: Optional[str] = None) -> str:
        """
        Return the system prompt for the Genie career chat agent.

        No user turn is returned — the caller appends the full conversation
        history before sending to the LLM.

        Args:
            resume_text: Optional resume excerpt to personalize advice.

        Returns:
            System prompt string.
        """
        base = (
            "You are Genie, an expert AI career coach specialising in the Indian job market — "
            "especially tech, automotive, EV, and manufacturing roles in Tamil Nadu and across India.\n\n"
            "Guidelines:\n"
            "- Be direct and practical. No generic platitudes or filler phrases.\n"
            "- Tailor every answer to the candidate's resume and situation when provided.\n"
            "- Topics you cover: resume improvements, salary negotiation, skill gap analysis, "
            "role transitions, interview preparation, job search strategy, LinkedIn optimisation.\n"
            "- Keep replies to 3-5 sentences unless the question genuinely requires more depth.\n"
            "- Use bullet points only when listing steps, options, or resources.\n"
            "- Always give the best answer you can — never deflect.\n"
            "- Salary figures should always be quoted in Indian Rupees (LPA or per month)."
        )
        if resume_text and resume_text.strip():
            base += f"\n\nCandidate resume (excerpt):\n{resume_text.strip()[:1500]}"
        return base
