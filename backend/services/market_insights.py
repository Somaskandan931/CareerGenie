"""
Market Insights service.
Uses pytrends (Google Trends) to fetch real trend data for tech skills/roles,
then uses Groq to generate a written market analysis.

Rate-limit handling:
  - Exponential back-off with jitter on 429 responses (up to 3 retries per chunk)
  - Polite inter-chunk delay (3–6 s) to avoid rapid-fire requests
  - In-memory cache (TTL = 6 h) so repeated calls for the same keywords
    never hit Google Trends again until the cache expires
"""
from groq import Groq
from typing import List, Dict, Optional
import logging
import json
import time
import random
import hashlib
import threading

from backend.config import settings

logger = logging.getLogger(__name__)

# ── In-memory trend cache (TTL = 6 hours) ─────────────────────────────────────
_trend_cache: Dict[str, Dict] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 6 * 3600


def _cache_key(keywords: List[str], timeframe: str) -> str:
    raw = "|".join(sorted(keywords)) + "|" + timeframe
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[Dict]:
    with _cache_lock:
        entry = _trend_cache.get(key)
        if entry and time.time() < entry["expires"]:
            return entry["data"]
        return None


def _cache_set(key: str, data: Dict) -> None:
    with _cache_lock:
        _trend_cache[key] = {"data": data, "expires": time.time() + _CACHE_TTL_SECONDS}


def _fetch_chunk_with_retry(keywords: List[str], timeframe: str,
                             max_retries: int = 3) -> Dict[str, List]:
    """
    Fetch one chunk (≤5 keywords) from Google Trends with exponential
    back-off on 429 / rate-limit errors.
    """
    from pytrends.request import TrendReq

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = (2 ** attempt) * random.uniform(1.0, 2.0)
                logger.info(f"Retry {attempt}/{max_retries} for {keywords} — waiting {delay:.1f}s")
                time.sleep(delay)

            # retries= and backoff_factor= are NOT passed to TrendReq because
            # they are forwarded to urllib3's Retry(), which renamed
            # method_whitelist → allowed_methods in urllib3 ≥ 2.0, causing:
            #   TypeError: Retry.__init__() got an unexpected keyword argument 'method_whitelist'
            # Our own retry loop above handles all retries instead.
            pt = TrendReq(
                hl='en-US',
                tz=330,
                timeout=(10, 25),
                requests_args={
                    'headers': {
                        'User-Agent': (
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/120.0.0.0 Safari/537.36'
                        )
                    }
                }
            )
            pt.build_payload(keywords, timeframe=timeframe, geo='IN')
            df = pt.interest_over_time()

            result: Dict[str, List] = {}
            if df.empty:
                for kw in keywords:
                    result[kw] = []
            else:
                for kw in keywords:
                    result[kw] = df[kw].tolist() if kw in df.columns else []
            return result

        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "Too Many Requests" in err_str
            if is_rate_limit and attempt < max_retries - 1:
                logger.warning(f"Rate-limited by Google Trends (attempt {attempt + 1}) — will retry")
                continue
            logger.warning(f"Trend fetch failed for {keywords}: {e}")
            return {kw: [] for kw in keywords}

    return {kw: [] for kw in keywords}


def _fetch_trends(keywords: List[str], timeframe: str = "today 12-m") -> Dict[str, List]:
    """
    Fetch Google Trends interest-over-time for a list of keywords.
    - Checks the 6-hour in-memory cache first.
    - Splits into chunks of ≤5 with polite inter-chunk delays.
    - Each chunk retried up to 3× with exponential back-off on 429s.
    - Falls back to empty lists if pytrends is unavailable.
    """
    ck = _cache_key(keywords, timeframe)
    cached = _cache_get(ck)
    if cached is not None:
        logger.info(f"Trend cache HIT for {len(keywords)} keywords")
        return cached

    try:
        import pytrends  # noqa — availability check only
    except ImportError:
        logger.warning("pytrends unavailable (No module named 'pytrends') — returning empty trends")
        return {kw: [] for kw in keywords}

    chunks = [keywords[i:i + 5] for i in range(0, len(keywords), 5)]
    all_data: Dict[str, List] = {}

    for idx, chunk in enumerate(chunks):
        if idx > 0:
            delay = random.uniform(3.0, 6.0)
            logger.info(f"Inter-chunk delay {delay:.1f}s before chunk {idx + 1}/{len(chunks)}")
            time.sleep(delay)
        all_data.update(_fetch_chunk_with_retry(chunk, timeframe))

    _cache_set(ck, all_data)
    logger.info(f"Trend cache SET for {len(keywords)} keywords (TTL {_CACHE_TTL_SECONDS // 3600}h)")
    return all_data


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