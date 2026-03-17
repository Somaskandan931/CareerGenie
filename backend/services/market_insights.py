"""
Market Insights service.
Uses pytrends (Google Trends) to fetch real trend data for tech skills/roles,
then uses Groq to generate a written market analysis.
"""
from groq import Groq
from typing import List, Dict, Optional
import logging
import json

from backend.config import settings

logger = logging.getLogger(__name__)


def _fetch_trends(keywords: List[str], timeframe: str = "today 12-m") -> Dict[str, List]:
    """
    Fetch Google Trends interest-over-time for a list of keywords.
    Returns dict: {keyword: [list of weekly interest values 0-100]}
    Falls back to empty dict if pytrends is unavailable or rate-limited.
    """
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl='en-US', tz=330)  # tz=330 → IST (India)
        # Google Trends accepts max 5 keywords per request
        chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
        all_data: Dict[str, List] = {}

        for chunk in chunks:
            pt.build_payload(chunk, timeframe=timeframe, geo='IN')
            df = pt.interest_over_time()
            if df.empty:
                for kw in chunk:
                    all_data[kw] = []
            else:
                for kw in chunk:
                    if kw in df.columns:
                        all_data[kw] = df[kw].tolist()
                    else:
                        all_data[kw] = []

        return all_data

    except Exception as e:
        logger.warning(f"pytrends unavailable ({e}) — returning empty trends")
        return {kw: [] for kw in keywords}


def _summarise_trend(values: List[int]) -> Dict:
    """Convert a list of weekly trend values into a simple summary dict."""
    if not values:
        return {"avg": 0, "peak": 0, "recent": 0, "direction": "unknown", "sparkline": []}
    avg = round(sum(values) / len(values), 1)
    peak = max(values)
    recent = round(sum(values[-4:]) / len(values[-4:]), 1) if len(values) >= 4 else values[-1]
    first_half = sum(values[:len(values)//2]) / (len(values)//2) if len(values) > 1 else avg
    second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if len(values) > 1 else avg
    direction = "rising" if second_half > first_half * 1.1 else "falling" if second_half < first_half * 0.9 else "stable"
    # Thin out sparkline to max 12 points for the UI
    step = max(1, len(values) // 12)
    sparkline = values[::step][-12:]
    return {"avg": avg, "peak": peak, "recent": recent, "direction": direction, "sparkline": sparkline}


class MarketInsights:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("MarketInsights initialized with Groq")

    def get_insights(self, role: str, skills: Optional[List[str]] = None,
                     location: str = "India") -> Dict:
        """
        Fetch Google Trends data for the role + top skills and generate
        an AI-written market analysis.

        Args:
            role: Target job role, e.g. "Machine Learning Engineer"
            skills: List of skills to track (max 10 used)
            location: For contextual analysis

        Returns:
            {
              "trend_data": {keyword: {avg, peak, recent, direction, sparkline}},
              "analysis": str,          # Groq-generated market analysis
              "hot_skills": [str],       # Skills with rising trends
              "timeframe": str
            }
        """
        # Build keyword list — role first, then skills
        keywords = [role]
        if skills:
            keywords += skills[:9]  # max 10 total
        keywords = list(dict.fromkeys(keywords))  # deduplicate, preserve order

        logger.info(f"Fetching trends for: {keywords}")
        raw_trends = _fetch_trends(keywords)
        trend_data = {kw: _summarise_trend(raw_trends.get(kw, [])) for kw in keywords}

        # Identify hot skills (rising or high avg)
        hot_skills = [kw for kw in keywords[1:] if trend_data[kw]["direction"] == "rising"
                      or trend_data[kw]["avg"] >= 50]

        analysis = self._generate_analysis(role, trend_data, hot_skills, location)

        return {
            "role": role,
            "location": location,
            "timeframe": "Past 12 months (Google Trends, India)",
            "trend_data": trend_data,
            "hot_skills": hot_skills,
            "analysis": analysis,
        }

    def _generate_analysis(self, role: str, trend_data: Dict, hot_skills: List[str],
                             location: str) -> str:
        # Build a compact summary of trends to feed to Groq
        trend_summary = "\n".join([
            f"- {kw}: avg interest {v['avg']}/100, direction={v['direction']}, peak={v['peak']}"
            for kw, v in trend_data.items()
        ])

        prompt = f"""You are a labour market analyst specialising in the Indian tech and manufacturing job market.

Role being analysed: {role}
Location context: {location}
Google Trends data (past 12 months, scale 0–100):
{trend_summary}
Hot/rising skills identified: {', '.join(hot_skills) if hot_skills else 'None identified'}

Write a 3-paragraph market analysis covering:
1. Current demand outlook for this role in {location} based on the trend data
2. Which skills are most in-demand and why (reference the trend data)
3. Salary expectations and career growth outlook for this role

Be specific, cite the trend data where relevant, and keep each paragraph to 3-4 sentences.
End with 3 bullet-point recommendations for job seekers targeting this role."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_INSIGHTS,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return f"Market analysis for {role} in {location} is currently unavailable. Please try again shortly."


_market_insights = None

def get_market_insights() -> MarketInsights:
    global _market_insights
    if _market_insights is None:
        _market_insights = MarketInsights()
    return _market_insights