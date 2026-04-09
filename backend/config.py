import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    # ── Ollama Configuration (Local LLM - Primary) ────────────────────────────
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "all-minilm")
    OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")

    # ── API Keys (Fallbacks if Ollama not available) ──────────────────────────
    SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # ── Groq Model Config (Fallback) ──────────────────────────────────────────
    GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
    GROQ_SMART_MODEL = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
    ]

    # ── Anthropic Model Config (Fallback) ─────────────────────────────────────
    ANTHROPIC_CHAT_MODEL = "claude-haiku-4-5"
    ANTHROPIC_SMART_MODEL = "claude-sonnet-4-5"
    ANTHROPIC_FALLBACK_MODELS = [
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
    ]

    # ── Gemini (Tertiary Fallback) ────────────────────────────────────────────
    GEMINI_CHAT_MODEL = "gemini-2.0-flash"
    GEMINI_SMART_MODEL = "gemini-2.0-flash"
    GEMINI_FALLBACK_MODELS = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    # ── Vector DB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fallback if Ollama not available

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
        "bms", "can bus", "plc", "cnc", "scada", "iatf", "lean manufacturing",
        "solidworks", "autocad", "catia", "embedded c", "microcontroller",
        "arduino", "stm32", "iot", "industry 4.0", "hydraulics", "pneumatics",
    ]

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []
        if not cls.SERPAPI_KEY:
            errors.append("SERPAPI_KEY not set in .env — get a free key at https://serpapi.com")
        if not cls.GROQ_API_KEY and not cls.ANTHROPIC_API_KEY and not cls.GEMINI_API_KEY:
            errors.append("No LLM API keys configured. Ollama will be used as primary (recommended).")
        return errors

    @classmethod
    def ensure_store_dirs(cls):
        """Create storage directories if they don't exist."""
        for d in (cls.FEEDBACK_STORE_DIR, cls.LTR_STORE_DIR):
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()