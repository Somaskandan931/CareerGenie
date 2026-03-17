import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    # ── API Keys ──────────────────────────────────────────────────────────────
    SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")

    # Groq replaces Anthropic for all LLM calls
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # ── Groq Model Config ─────────────────────────────────────────────────────
    # Fast model for chat / explanations (low latency)
    GROQ_CHAT_MODEL = "llama-3.1-8b-instant"
    # Smarter model for roadmaps, projects, career advice (higher quality)
    GROQ_SMART_MODEL = "llama-3.3-70b-versatile"

    # ── Vector DB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # ── Job Search Defaults ───────────────────────────────────────────────────
    DEFAULT_NUM_JOBS = 50
    DEFAULT_TOP_K = 10

    # ── Token Limits ──────────────────────────────────────────────────────────
    MAX_TOKENS_CAREER_ADVICE = 2000
    MAX_TOKENS_ROADMAP = 6000       # increased: 70b model needs room for full JSON roadmap
    MAX_TOKENS_CHAT = 1024          # job coach / interview coach responses
    MAX_TOKENS_INSIGHTS = 1500      # market insights

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
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY not set in .env")
        return errors


settings = Settings()