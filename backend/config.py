import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    # ── API Keys ──────────────────────────────────────────────────────────────
    SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")

    # Google Gemini — primary LLM provider (free tier, no daily token cap)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # ── Gemini Model Config ───────────────────────────────────────────────────
    # Fast model for chat / explanations (free tier, high rate limits)
    GEMINI_CHAT_MODEL = "gemini-2.5-flash"
    # Smarter model for roadmaps, projects, career advice, debate (free tier)
    GEMINI_SMART_MODEL = "gemini-2.5-flash"

    # ── Vector DB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # ── Job Search Defaults ───────────────────────────────────────────────────
    DEFAULT_NUM_JOBS = 50
    DEFAULT_TOP_K = 10

    # ── Token Limits ──────────────────────────────────────────────────────────
    MAX_TOKENS_CAREER_ADVICE = 2000
    MAX_TOKENS_ROADMAP = 6000
    MAX_TOKENS_CHAT = 1024
    MAX_TOKENS_INSIGHTS = 1500

    # ── Feedback & Learning Engine Storage ────────────────────────────────────
    FEEDBACK_STORE_DIR = os.getenv(
        "FEEDBACK_STORE_DIR",
        str(Path(__file__).parent.parent / "tmp" / "career_genie_feedback")
    )

    # ── Learning-to-Rank Storage ──────────────────────────────────────────────
    LTR_STORE_DIR = os.getenv(
        "LTR_STORE_DIR",
        str(Path(__file__).parent.parent / "tmp" / "career_genie_ltr")
    )

    # ── Tech Skills for Career Advisor ───────────────────────────────────────
    TECH_SKILLS = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby",
        "go", "rust", "php", "swift", "kotlin", "scala", "r",
        "react", "angular", "vue", "svelte", "html", "css", "sass",
        "tailwind", "bootstrap", "webpack", "vite",
        "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring boot",
        "asp.net", "rails", "laravel", "nest.js",
        "sql", "mysql", "postgresql", "mongodb", "redis", "dynamodb",
        "oracle", "cassandra", "elasticsearch", "firebase",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
        "terraform", "ansible", "ci/cd", "github actions", "gitlab ci",
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "pandas", "numpy", "matplotlib", "nlp",
        "computer vision", "data analysis", "statistics",
        "git", "jira", "confluence", "linux", "bash", "agile", "scrum",
        "rest api", "restful", "graphql", "microservices", "system design",
        "testing", "jest", "pytest", "selenium", "unit testing",
        # TN Automotive / EV additions
        "bms", "can bus", "plc", "cnc", "scada", "iatf", "lean manufacturing",
        "solidworks", "autocad", "catia", "embedded c", "microcontroller",
        "arduino", "stm32", "iot", "industry 4.0", "hydraulics", "pneumatics",
    ]

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []
        if not cls.SERPAPI_KEY:
            errors.append("SERPAPI_KEY or SEARCHAPI_KEY not set in .env")
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY not set in .env")
        return errors

    @classmethod
    def ensure_store_dirs(cls):
        """Create storage directories if they don't exist."""
        for d in (cls.FEEDBACK_STORE_DIR, cls.LTR_STORE_DIR):
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()