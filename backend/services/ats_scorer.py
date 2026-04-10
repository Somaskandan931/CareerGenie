from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings
from backend.services.llm import llm_call_sync, llm_call_smart_sync

logger = logging.getLogger( __name__ )


class ATSScorer :
    def __init__ ( self ) :
        pass

    def score_resume ( self, resume_text: str, target_role: str = "Software Engineer",
                       job_description: Optional[str] = None ) -> Dict :
        """
        Analyse a resume and return a structured ATS-style evaluation.
        If job_description is provided, score against that specific job.
        Returns strict JSON matching the ATSScoreResult schema.
        """

        # Build prompt based on whether job_description is provided
        if job_description and job_description.strip() :
            prompt = f"""You are an expert ATS analyzer. Return ONLY valid JSON.

CRITICAL JSON RULES:
- Use double quotes for all strings
- No trailing commas
- Escape double quotes inside strings with backslash
- Keep all content on single lines

JOB DESCRIPTION:
{job_description[:3000]}

TARGET ROLE: "{target_role}"

RESUME:
{resume_text[:4000]}

Return EXACTLY this JSON structure (replace values with your analysis):
{{"overall_score": 75, "keyword_score": 70, "format_score": 80, "missing_keywords": ["skill1", "skill2"], "found_keywords": ["skill3", "skill4"], "section_feedback": {{"experience": "feedback here", "skills": "feedback here", "education": "feedback here", "summary": "feedback here", "formatting": "feedback here"}}, "bullet_quality": {{"score": 70, "issues": ["issue1"], "good_examples": ["example1"]}}, "improvements": ["improvement1", "improvement2", "improvement3", "improvement4", "improvement5", "improvement6"], "ats_verdict": "Good", "verdict_reason": "reason here"}}"""
        else :
            prompt = f"""You are an expert ATS analyzer. Return ONLY valid JSON.

CRITICAL JSON RULES:
- Use double quotes for all strings
- No trailing commas
- Escape double quotes inside strings with backslash
- Keep all content on single lines

TARGET ROLE: "{target_role}"

RESUME:
{resume_text[:4000]}

Return EXACTLY this JSON structure (replace values with your analysis):
{{"overall_score": 75, "keyword_score": 70, "format_score": 80, "missing_keywords": ["skill1", "skill2"], "found_keywords": ["skill3", "skill4"], "section_feedback": {{"experience": "feedback here", "skills": "feedback here", "education": "feedback here", "summary": "feedback here", "formatting": "feedback here"}}, "bullet_quality": {{"score": 70, "issues": ["issue1"], "good_examples": ["example1"]}}, "improvements": ["improvement1", "improvement2", "improvement3", "improvement4", "improvement5", "improvement6"], "ats_verdict": "Good", "verdict_reason": "reason here"}}"""

        try :
            raw = llm_call_sync(
                system="You are an expert AI assistant. Respond with ONLY valid JSON. No markdown, no explanations, no extra text.",
                user=prompt,
                temp=0.2,
                max_tokens=1500,
            )

            # Clean the response
            raw = self._clean_response( raw )

            if not raw :
                logger.error( "Empty response from LLM" )
                return self._fallback_result( resume_text, target_role, job_description )

            # Parse JSON
            result = self._parse_json_response( raw )

            if result and isinstance( result, dict ) :
                return self._validate_result( result, target_role )
            else :
                logger.warning( f"Invalid result type: {type( result )}" )
                return self._fallback_result( resume_text, target_role, job_description )

        except Exception as e :
            logger.error( f"ATS score error: {e}" )
            return self._fallback_result( resume_text, target_role, job_description )

    def score ( self, resume_text: str, target_role: str = "Software Engineer",
                job_description: str = "" ) -> Dict :
        """Alias for score_resume method."""
        jd = job_description if job_description and job_description.strip() else None
        return self.score_resume( resume_text, target_role, jd )

    def _clean_response ( self, raw: str ) -> str :
        """Clean LLM response for JSON parsing."""
        if not raw :
            return ""

        # Remove markdown code blocks
        raw = re.sub( r'```json\s*', '', raw )
        raw = re.sub( r'```\s*', '', raw )

        # Find JSON object - from first { to last }
        start = raw.find( '{' )
        end = raw.rfind( '}' )

        if start >= 0 and end > start :
            raw = raw[start :end + 1]
        else :
            return ""

        # Remove trailing commas before } or ]
        raw = re.sub( r',\s*}', '}', raw )
        raw = re.sub( r',\s*]', ']', raw )

        return raw.strip()

    def _parse_json_response ( self, raw: str ) -> Optional[Dict] :
        """Parse JSON response with multiple strategies."""
        if not raw :
            return None

        # Strategy 1: Direct parse
        try :
            return json.loads( raw )
        except json.JSONDecodeError as e :
            logger.debug( f"Direct parse failed: {e}" )

        # Strategy 2: Try to complete truncated JSON
        try :
            # Check if JSON is truncated (missing closing braces)
            open_braces = raw.count( '{' )
            close_braces = raw.count( '}' )

            if open_braces > close_braces :
                # Add missing closing braces
                raw += '}' * (open_braces - close_braces)
                return json.loads( raw )
        except json.JSONDecodeError :
            pass

        # Strategy 3: Fix common issues
        try :
            # Replace single quotes
            fixed = raw.replace( "'", '"' )
            # Fix missing quotes around keys
            fixed = re.sub( r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed )
            # Remove trailing commas
            fixed = re.sub( r',\s*}', '}', fixed )
            fixed = re.sub( r',\s*]', ']', fixed )
            return json.loads( fixed )
        except json.JSONDecodeError as e :
            logger.debug( f"Fixed parse failed: {e}" )

        # Strategy 4: Try to extract partial data
        try :
            # Get whatever we can from the partial JSON
            result = {}

            # Extract overall_score
            score_match = re.search( r'"overall_score":\s*(\d+)', raw )
            if score_match :
                result["overall_score"] = int( score_match.group( 1 ) )

            # Extract keyword_score
            kw_match = re.search( r'"keyword_score":\s*(\d+)', raw )
            if kw_match :
                result["keyword_score"] = int( kw_match.group( 1 ) )

            # Extract format_score
            fmt_match = re.search( r'"format_score":\s*(\d+)', raw )
            if fmt_match :
                result["format_score"] = int( fmt_match.group( 1 ) )

            # Extract missing_keywords
            missing_match = re.search( r'"missing_keywords":\s*\[(.*?)\]', raw, re.DOTALL )
            if missing_match :
                keywords_str = missing_match.group( 1 )
                keywords = re.findall( r'"([^"]*)"', keywords_str )
                result["missing_keywords"] = keywords

            # Extract found_keywords
            found_match = re.search( r'"found_keywords":\s*\[(.*?)\]', raw, re.DOTALL )
            if found_match :
                keywords_str = found_match.group( 1 )
                keywords = re.findall( r'"([^"]*)"', keywords_str )
                result["found_keywords"] = keywords

            # Extract improvements
            improvements_match = re.search( r'"improvements":\s*\[(.*?)\]', raw, re.DOTALL )
            if improvements_match :
                improvements_str = improvements_match.group( 1 )
                improvements = re.findall( r'"([^"]*)"', improvements_str )
                result["improvements"] = improvements

            # Extract ats_verdict
            verdict_match = re.search( r'"ats_verdict":\s*"([^"]*)"', raw )
            if verdict_match :
                result["ats_verdict"] = verdict_match.group( 1 )

            # Extract verdict_reason
            reason_match = re.search( r'"verdict_reason":\s*"([^"]*)"', raw )
            if reason_match :
                result["verdict_reason"] = reason_match.group( 1 )

            if result :
                return result
        except Exception as e :
            logger.debug( f"Partial extraction failed: {e}" )

        logger.error( f"All parsing strategies failed. Raw: {raw[:200]}" )
        return None

    def _validate_result ( self, result: Dict, target_role: str ) -> Dict :
        """Ensure all required fields exist with correct types."""
        defaults = {
            "overall_score" : 50,
            "keyword_score" : 50,
            "format_score" : 60,
            "missing_keywords" : [],
            "found_keywords" : [],
            "section_feedback" : {
                "experience" : "Review your experience section.",
                "skills" : "Ensure skills match the target role.",
                "education" : "Education section looks adequate.",
                "summary" : "Consider adding a professional summary.",
                "formatting" : "Check ATS compatibility.",
            },
            "bullet_quality" : {"score" : 50, "issues" : [], "good_examples" : []},
            "improvements" : ["Tailor resume to job description"],
            "ats_verdict" : "Needs Work",
            "verdict_reason" : "Resume requires optimization for ATS systems.",
        }

        # Merge with defaults
        for key, val in defaults.items() :
            if key not in result or result[key] is None :
                result[key] = val

        # Ensure section_feedback has all subfields
        if not isinstance( result.get( "section_feedback" ), dict ) :
            result["section_feedback"] = defaults["section_feedback"]
        else :
            for subkey in defaults["section_feedback"] :
                if subkey not in result["section_feedback"] or not result["section_feedback"][subkey] :
                    result["section_feedback"][subkey] = defaults["section_feedback"][subkey]

        # Ensure bullet_quality has all subfields
        if not isinstance( result.get( "bullet_quality" ), dict ) :
            result["bullet_quality"] = defaults["bullet_quality"]
        else :
            for subkey in defaults["bullet_quality"] :
                if subkey not in result["bullet_quality"] :
                    result["bullet_quality"][subkey] = defaults["bullet_quality"][subkey]

        # Ensure improvements is a list
        if not isinstance( result.get( "improvements" ), list ) :
            result["improvements"] = defaults["improvements"]
        elif len( result["improvements"] ) < 3 :
            result["improvements"].extend( defaults["improvements"][len( result["improvements"] ) :] )

        # Clamp scores
        for score_key in ("overall_score", "keyword_score", "format_score") :
            if score_key in result :
                try :
                    val = int( result[score_key] )
                    result[score_key] = max( 0, min( 100, val ) )
                except (ValueError, TypeError) :
                    result[score_key] = 50

        if "score" in result.get( "bullet_quality", {} ) :
            try :
                val = int( result["bullet_quality"]["score"] )
                result["bullet_quality"]["score"] = max( 0, min( 100, val ) )
            except (ValueError, TypeError) :
                result["bullet_quality"]["score"] = 50

        return result

    def _fallback_result ( self, resume_text: str, target_role: str, job_description: Optional[str] = None ) -> Dict :
        """Generate a fallback result when API calls fail."""
        word_count = len( resume_text.split() )
        score = min( 60, max( 20, word_count // 5 ) )

        missing_keywords = ["quantified achievements", "action verbs", "technical skills", "certifications",
                            "leadership", "metrics"]
        found_keywords = []

        # If job description is provided, extract some basic keywords from it
        if job_description and job_description.strip() :
            words = job_description.lower().split()
            common_skills = [s for s in settings.TECH_SKILLS if s.lower() in ' '.join( words )]
            missing_keywords = common_skills[:8] if common_skills else missing_keywords

        return {
            "overall_score" : score,
            "keyword_score" : score - 10,
            "format_score" : 55,
            "missing_keywords" : missing_keywords,
            "found_keywords" : found_keywords,
            "section_feedback" : {
                "experience" : "Unable to fully analyze. Ensure experience is clearly formatted with bullet points.",
                "skills" : "Add a dedicated skills section with relevant technical and soft skills.",
                "education" : "Include degree, institution, and graduation year.",
                "summary" : "Add a 2-3 sentence professional summary at the top.",
                "formatting" : "Use standard section headers and avoid tables/columns for ATS compatibility.",
            },
            "bullet_quality" : {
                "score" : 40,
                "issues" : ["Missing quantified metrics", "Weak action verbs", "Too vague — be more specific"],
                "good_examples" : [],
            },
            "improvements" : [
                "Add quantified achievements (e.g., 'Increased sales by 30%')",
                "Use strong action verbs (Led, Built, Optimized, Delivered)",
                f"Add role-specific keywords for {target_role}",
                "Include a professional summary section",
                "Ensure consistent date formatting throughout",
                "Remove tables and columns for better ATS parsing",
            ],
            "ats_verdict" : "Needs Work",
            "verdict_reason" : "Resume needs keyword optimization and stronger impact statements.",
        }


# Singleton instance
try :
    ats_scorer = ATSScorer()
except Exception as e :
    logger.error( f"Failed to initialize ATSScorer: {e}" )
    ats_scorer = None


def get_ats_scorer () -> ATSScorer :
    """Return the singleton ATSScorer instance."""
    global ats_scorer
    if ats_scorer is None :
        ats_scorer = ATSScorer()
    return ats_scorer