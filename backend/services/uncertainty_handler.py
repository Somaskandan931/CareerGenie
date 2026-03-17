"""
Uncertainty Handler
====================
Addresses the critique:
  ❌ "Everything assumes resume parsing is correct"
  ❌ "Skill extraction is assumed correct"
  ❌ "LLM outputs are assumed reliable"
  ❌ "Your system will silently fail"

What we implement:
  1. Output confidence scoring   — every LLM-generated result gets a
                                   confidence score based on structural
                                   completeness, internal consistency,
                                   and field coverage

  2. Parse quality assessment    — resume parsing is scored on text
                                   density, section detection, and
                                   encoding artefacts

  3. Skill extraction validation — extracted skills are checked against
                                   known taxonomy; low coverage triggers
                                   a warning

  4. LLM output calibration      — detects hallucination signals:
                                   generic filler text, missing required
                                   fields, implausible numeric values

  5. Graceful degradation tiers  — instead of silent failure, every
                                   uncertain result is tagged with a
                                   confidence tier and a human-readable
                                   explanation so the UI can show
                                   appropriate caveats

  6. Consistency checker         — cross-validates outputs from different
                                   agents against each other
                                   (e.g. career_advice skill gaps vs
                                   ats_score missing_keywords)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Confidence tiers ───────────────────────────────────────────────────────────

HIGH_CONFIDENCE   = "high"    # ≥ 0.75 — show normally
MEDIUM_CONFIDENCE = "medium"  # 0.50–0.74 — show with note
LOW_CONFIDENCE    = "low"     # 0.25–0.49 — show with warning
UNRELIABLE        = "unreliable"  # < 0.25 — show fallback / ask for retry

TIER_THRESHOLDS = {
    HIGH_CONFIDENCE:   0.75,
    MEDIUM_CONFIDENCE: 0.50,
    LOW_CONFIDENCE:    0.25,
}


@dataclass
class ConfidenceReport:
    score:       float           # 0.0 – 1.0
    tier:        str             # high / medium / low / unreliable
    issues:      List[str] = field(default_factory=list)
    warnings:    List[str] = field(default_factory=list)
    passed:      List[str] = field(default_factory=list)
    should_retry: bool = False
    fallback_used: bool = False

    def to_dict(self) -> Dict:
        return {
            "confidence_score":  round(self.score, 3),
            "confidence_tier":   self.tier,
            "issues":            self.issues,
            "warnings":          self.warnings,
            "passed_checks":     self.passed,
            "should_retry":      self.should_retry,
            "fallback_used":     self.fallback_used,
        }


def _tier(score: float) -> str:
    if score >= TIER_THRESHOLDS[HIGH_CONFIDENCE]:
        return HIGH_CONFIDENCE
    if score >= TIER_THRESHOLDS[MEDIUM_CONFIDENCE]:
        return MEDIUM_CONFIDENCE
    if score >= TIER_THRESHOLDS[LOW_CONFIDENCE]:
        return LOW_CONFIDENCE
    return UNRELIABLE


# ── Resume parse quality ───────────────────────────────────────────────────────

class ResumeParseValidator:
    """Validates that resume text extraction actually worked."""

    EXPECTED_SECTIONS = [
        "experience", "education", "skills", "project",
        "summary", "objective", "work", "employment",
    ]
    NOISE_PATTERNS = [
        r'[\x00-\x08\x0b\x0c\x0e-\x1f]',   # control characters
        r'[^\x00-\x7F]{3,}',                 # long non-ASCII runs
    ]
    MIN_WORDS    = 80
    MIN_SECTIONS = 2

    def validate(self, resume_text: str, word_count: int) -> ConfidenceReport:
        issues   = []
        warnings = []
        passed   = []
        score    = 1.0

        # ── Word count ────────────────────────────────────────────────────────
        if word_count < self.MIN_WORDS:
            issues.append(f"Very short resume ({word_count} words). Parsing may have missed content.")
            score -= 0.30
        elif word_count < 150:
            warnings.append(f"Short resume ({word_count} words). Consider adding more detail.")
            score -= 0.10
        else:
            passed.append(f"Adequate length ({word_count} words)")

        # ── Section detection ─────────────────────────────────────────────────
        text_lower = resume_text.lower()
        found_sections = [s for s in self.EXPECTED_SECTIONS if s in text_lower]
        if len(found_sections) < self.MIN_SECTIONS:
            issues.append(
                f"Only {len(found_sections)} standard section(s) detected. "
                "Resume may be in an unsupported format (table/image-based PDF)."
            )
            score -= 0.25
        else:
            passed.append(f"Detected {len(found_sections)} standard sections: {', '.join(found_sections)}")

        # ── Noise / encoding artefacts ────────────────────────────────────────
        for pattern in self.NOISE_PATTERNS:
            matches = re.findall(pattern, resume_text)
            if len(matches) > 5:
                warnings.append(
                    f"Encoding artefacts detected ({len(matches)} occurrences). "
                    "Consider re-uploading as plain-text PDF."
                )
                score -= 0.10
                break
        else:
            passed.append("No encoding artefacts")

        # ── Contact info presence ─────────────────────────────────────────────
        has_email = bool(re.search(r'[\w.]+@[\w.]+\.\w+', resume_text))
        if not has_email:
            warnings.append("No email address detected. Resume may be incomplete.")
            score -= 0.05
        else:
            passed.append("Contact information present")

        score = max(0.0, min(1.0, score))
        report = ConfidenceReport(
            score=score, tier=_tier(score),
            issues=issues, warnings=warnings, passed=passed,
            should_retry=score < 0.5,
        )
        return report


# ── Skill extraction validator ─────────────────────────────────────────────────

class SkillExtractionValidator:
    """Validates that skill extraction produced plausible results."""

    KNOWN_SKILLS = {
        "python", "java", "javascript", "typescript", "sql", "aws", "azure",
        "docker", "kubernetes", "react", "tensorflow", "pytorch", "git",
        "linux", "machine learning", "deep learning", "fastapi", "django",
        "flask", "mongodb", "postgresql", "redis", "spark", "scala", "go",
        "rust", "c++", "c#", "spring", "node.js", "angular", "vue",
    }
    MIN_SKILLS = 2
    MAX_REASONABLE = 30

    def validate(self, extracted_skills: List[Any], resume_text: str) -> ConfidenceReport:
        issues   = []
        warnings = []
        passed   = []
        score    = 1.0

        skill_names = []
        for s in extracted_skills:
            if isinstance(s, dict):
                skill_names.append(s.get("skill", s.get("variation", "")).lower())
            elif isinstance(s, str):
                skill_names.append(s.lower())

        n = len(skill_names)

        # ── Count check ───────────────────────────────────────────────────────
        if n < self.MIN_SKILLS:
            issues.append(
                f"Only {n} skill(s) extracted. Resume may lack a skills section "
                "or use non-standard formatting."
            )
            score -= 0.35
        elif n > self.MAX_REASONABLE:
            warnings.append(f"Unusually high skill count ({n}). Some extracted terms may be noise.")
            score -= 0.10
        else:
            passed.append(f"{n} skills extracted")

        # ── Known taxonomy coverage ───────────────────────────────────────────
        recognised = [s for s in skill_names if any(k in s for k in self.KNOWN_SKILLS)]
        if n > 0:
            coverage = len(recognised) / n
            if coverage < 0.4:
                warnings.append(
                    f"Low taxonomy coverage ({coverage:.0%} of extracted skills are recognised). "
                    "Skills may be domain-specific or non-standard."
                )
                score -= 0.15
            else:
                passed.append(f"Taxonomy coverage: {coverage:.0%}")

        # ── Resume text cross-check ───────────────────────────────────────────
        text_lower = resume_text.lower()
        phantom    = [s for s in skill_names if s not in text_lower]
        if phantom:
            issues.append(
                f"{len(phantom)} extracted skill(s) not found in resume text: {phantom[:3]}. "
                "Possible extraction error."
            )
            score -= 0.20

        score = max(0.0, min(1.0, score))
        return ConfidenceReport(
            score=score, tier=_tier(score),
            issues=issues, warnings=warnings, passed=passed,
            should_retry=score < 0.45,
        )


# ── LLM output validator ───────────────────────────────────────────────────────

class LLMOutputValidator:
    """
    Detects hallucination signals and validates LLM-generated structured outputs.
    """

    FILLER_PHRASES = [
        "lorem ipsum", "placeholder", "insert here", "to be determined",
        "example company", "your name", "sample text", "n/a", "none provided",
        "[company]", "[role]", "[skill]",
    ]

    def validate_ats_score(self, result: Dict) -> ConfidenceReport:
        return self._validate_structured(
            result,
            required_fields=["overall_score", "missing_keywords", "improvements", "ats_verdict"],
            numeric_range_checks={"overall_score": (0, 100), "keyword_score": (0, 100)},
            list_min_lengths={"improvements": 2, "missing_keywords": 1},
            name="ATS Score",
        )

    def validate_career_advice(self, result: Dict) -> ConfidenceReport:
        return self._validate_structured(
            result,
            required_fields=["current_assessment", "skill_gaps", "action_plan"],
            list_min_lengths={"skill_gaps": 1, "action_plan": 2},
            name="Career Advice",
        )

    def validate_job_matches(self, matches: List[Dict]) -> ConfidenceReport:
        issues   = []
        warnings = []
        passed   = []
        score    = 1.0

        if not matches:
            return ConfidenceReport(
                score=0.1, tier=UNRELIABLE,
                issues=["No job matches returned. Vector store may be empty."],
                should_retry=True,
            )

        # Check score distribution — if all scores are the same, something is wrong
        scores = [m.get("match_score", 0) for m in matches]
        if len(set(scores)) == 1:
            issues.append("All match scores are identical — scoring may have failed.")
            score -= 0.30

        # Check for required fields
        missing_fields = [
            f for f in ("title", "company", "match_score")
            if not all(f in m for m in matches)
        ]
        if missing_fields:
            issues.append(f"Some matches missing required fields: {missing_fields}")
            score -= 0.20
        else:
            passed.append("All required fields present")

        # Check for implausible scores
        implausible = [m for m in matches if m.get("match_score", 0) > 100 or m.get("match_score", 0) < 0]
        if implausible:
            issues.append(f"{len(implausible)} match(es) have out-of-range scores")
            score -= 0.15

        if len(matches) >= 3:
            passed.append(f"{len(matches)} matches returned")

        score = max(0.0, min(1.0, score))
        return ConfidenceReport(
            score=score, tier=_tier(score),
            issues=issues, warnings=warnings, passed=passed,
        )

    def validate_roadmap(self, roadmap: Dict) -> ConfidenceReport:
        return self._validate_structured(
            roadmap,
            required_fields=["phases", "title", "duration_weeks"],
            list_min_lengths={"phases": 1},
            name="Roadmap",
        )

    def _validate_structured(
        self,
        result: Dict,
        required_fields: List[str],
        numeric_range_checks: Optional[Dict[str, Tuple]] = None,
        list_min_lengths: Optional[Dict[str, int]] = None,
        name: str = "Output",
    ) -> ConfidenceReport:
        issues   = []
        warnings = []
        passed   = []
        score    = 1.0

        if not result:
            return ConfidenceReport(
                score=0.0, tier=UNRELIABLE,
                issues=[f"{name}: Empty result returned"],
                should_retry=True,
            )

        # ── Required fields ───────────────────────────────────────────────────
        missing = [f for f in required_fields if f not in result or result[f] is None]
        if missing:
            issues.append(f"{name} missing required fields: {missing}")
            score -= 0.15 * len(missing)
        else:
            passed.append("All required fields present")

        # ── Numeric range checks ──────────────────────────────────────────────
        for field_name, (lo, hi) in (numeric_range_checks or {}).items():
            val = result.get(field_name)
            if val is not None and not (lo <= val <= hi):
                issues.append(f"{name}.{field_name}={val} is outside expected range [{lo},{hi}]")
                score -= 0.10

        # ── List minimum lengths ──────────────────────────────────────────────
        for field_name, min_len in (list_min_lengths or {}).items():
            lst = result.get(field_name, [])
            if isinstance(lst, list) and len(lst) < min_len:
                warnings.append(
                    f"{name}.{field_name} has only {len(lst)} item(s) (expected ≥ {min_len})"
                )
                score -= 0.08

        # ── Filler text detection ─────────────────────────────────────────────
        result_str = str(result).lower()
        fillers    = [f for f in self.FILLER_PHRASES if f in result_str]
        if fillers:
            issues.append(f"{name} contains placeholder/filler text: {fillers[:3]}")
            score -= 0.20

        # ── Suspiciously short text fields ────────────────────────────────────
        for k, v in result.items():
            if isinstance(v, str) and 0 < len(v) < 10:
                warnings.append(f"{name}.{k} is suspiciously short: '{v}'")
                score -= 0.05

        score = max(0.0, min(1.0, score))
        return ConfidenceReport(
            score=score, tier=_tier(score),
            issues=issues, warnings=warnings, passed=passed,
            should_retry=score < 0.45,
        )


# ── Cross-agent consistency checker ───────────────────────────────────────────

class ConsistencyChecker:
    """
    Cross-validates outputs from different agents against each other.
    Catches contradictions that would confuse the user.
    """

    def check(self, memory_snapshot: Dict) -> Dict:
        """
        Check consistency across all outputs in the agent memory snapshot.
        Returns a consistency report with any contradictions flagged.
        """
        issues   = []
        warnings = []

        ats     = memory_snapshot.get("ats_score",     {})
        advice  = memory_snapshot.get("career_advice", {})
        matches = memory_snapshot.get("job_matches",   [])
        gaps    = memory_snapshot.get("skill_gaps",    [])

        # ── ATS missing keywords vs skill gaps ────────────────────────────────
        ats_missing = set(kw.lower() for kw in ats.get("missing_keywords", []))
        gap_skills  = set(
            g["skill"].lower() if isinstance(g, dict) else g.lower()
            for g in gaps
        )
        advisor_gaps = set(
            g["skill"].lower() if isinstance(g, dict) else g.lower()
            for g in advice.get("skill_gaps", [])
        )

        if ats_missing and advisor_gaps:
            overlap = ats_missing & advisor_gaps
            if not overlap and len(ats_missing) > 2:
                warnings.append(
                    "ATS missing keywords and career advisor skill gaps do not overlap — "
                    "they may be analysing different aspects. Review both carefully."
                )
            else:
                pass  # Good — they agree

        # ── Job match scores vs ATS score ─────────────────────────────────────
        ats_overall = ats.get("overall_score", 0)
        if matches and ats_overall > 0:
            top_match = max(matches, key=lambda m: m.get("match_score", 0), default={})
            top_score = top_match.get("match_score", 0)

            if ats_overall < 30 and top_score > 70:
                warnings.append(
                    f"ATS score is low ({ats_overall}/100) but top job match is "
                    f"high ({top_score}%). The resume may match job keywords but "
                    "fail ATS formatting requirements."
                )

        # ── Advisor action plan vs job matches ────────────────────────────────
        action_plan = advice.get("action_plan", [])
        if matches and not action_plan:
            warnings.append(
                "Job matches were found but the career advisor produced no action plan. "
                "The advisor may have insufficient context."
            )

        return {
            "consistent":   len(issues) == 0,
            "issues":       issues,
            "warnings":     warnings,
            "checks_run":   [
                "ats_vs_skill_gaps",
                "match_score_vs_ats",
                "action_plan_coverage",
            ],
        }


# ── Uncertainty-aware wrapper ──────────────────────────────────────────────────

class UncertaintyHandler:
    """
    Wraps any service call with confidence validation.
    Provides a single entry point for all uncertainty checks.

    Usage:
        uh = get_uncertainty_handler()

        # Wrap resume parsing
        text, report = uh.wrap_parse(resume_text, word_count)

        # Wrap LLM outputs
        ats_result, report = uh.wrap_ats(raw_ats_result)
        advice, report = uh.wrap_advice(raw_advice)
        matches, report = uh.wrap_matches(raw_matches)
        roadmap, report = uh.wrap_roadmap(raw_roadmap)
        skills, report = uh.wrap_skills(extracted_skills, resume_text)

        # Cross-agent consistency
        consistency = uh.check_consistency(memory_snapshot)
    """

    def __init__(self):
        self.resume_validator = ResumeParseValidator()
        self.skill_validator  = SkillExtractionValidator()
        self.llm_validator    = LLMOutputValidator()
        self.consistency      = ConsistencyChecker()

    def wrap_parse(
        self, resume_text: str, word_count: int
    ) -> Tuple[str, ConfidenceReport]:
        report = self.resume_validator.validate(resume_text, word_count)
        return resume_text, report

    def wrap_ats(self, result: Dict) -> Tuple[Dict, ConfidenceReport]:
        report = self.llm_validator.validate_ats_score(result)
        return result, report

    def wrap_advice(self, result: Dict) -> Tuple[Dict, ConfidenceReport]:
        report = self.llm_validator.validate_career_advice(result)
        return result, report

    def wrap_matches(self, matches: List[Dict]) -> Tuple[List[Dict], ConfidenceReport]:
        report = self.llm_validator.validate_job_matches(matches)
        return matches, report

    def wrap_roadmap(self, roadmap: Dict) -> Tuple[Dict, ConfidenceReport]:
        report = self.llm_validator.validate_roadmap(roadmap)
        return roadmap, report

    def wrap_skills(
        self, skills: List[Any], resume_text: str
    ) -> Tuple[List[Any], ConfidenceReport]:
        report = self.skill_validator.validate(skills, resume_text)
        return skills, report

    def check_consistency(self, memory_snapshot: Dict) -> Dict:
        return self.consistency.check(memory_snapshot)

    def annotate(self, result: Any, report: ConfidenceReport) -> Dict:
        """
        Attach confidence metadata to any result dict so the frontend
        can display appropriate caveats without changing business logic.
        """
        if isinstance(result, dict):
            return {**result, "_confidence": report.to_dict()}
        return {"data": result, "_confidence": report.to_dict()}


# ── Singleton ──────────────────────────────────────────────────────────────────
_uncertainty_handler: Optional[UncertaintyHandler] = None


def get_uncertainty_handler() -> UncertaintyHandler:
    global _uncertainty_handler
    if _uncertainty_handler is None:
        _uncertainty_handler = UncertaintyHandler()
    return _uncertainty_handler