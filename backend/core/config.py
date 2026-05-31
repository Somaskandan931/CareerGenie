"""
backend/core/config.py
======================
Pydantic-Settings based configuration for Career Genie.

All values come from environment variables or ``backend/.env``.
Never hard-code secrets anywhere else in the codebase.

Usage::

    from backend.core.config import settings

    print(settings.GROQ_API_KEY)
    settings.ensure_directories()

    # Check for non-fatal warnings at startup
    for warning in settings.validate_config():
        logger.warning(warning)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# ── Load .env before Pydantic instantiates Settings ──────────────────────────
_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

# ── Pydantic v1 / v2 compatibility ───────────────────────────────────────────
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _PYDANTIC_V2 = True
except ImportError:                                   # pragma: no cover
    from pydantic import BaseSettings                 # type: ignore[no-redef]
    _PYDANTIC_V2 = False


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Typed, validated configuration for Career Genie.

    Every field maps 1-to-1 to an environment variable (case-insensitive).
    ``Optional`` fields default to ``None`` and **must** be checked before use.
    """

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "Career Genie AI"
    APP_VERSION: str = "3.1.0"
    #: "development" | "production" — controls CORS, rate-limiting warnings, etc.
    DEPLOYMENT_MODE: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Ollama (local LLM — primary inference) ────────────────────────────────
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "all-minilm"
    OLLAMA_LLM_MODEL: str = "llama3.2:3b"

    # ── External API keys ─────────────────────────────────────────────────────
    #: SerpAPI key for job search.  Falls back to SEARCHAPI_KEY if unset.
    SERPAPI_KEY: Optional[str] = None
    SEARCHAPI_KEY: Optional[str] = None   # alias / fallback
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    # Gemini intentionally omitted from provider waterfall (removed in v3.1)

    # ── Groq models ───────────────────────────────────────────────────────────
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_SMART_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODELS: List[str] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
    ]

    # ── Anthropic models ──────────────────────────────────────────────────────
    ANTHROPIC_CHAT_MODEL: str = "claude-haiku-4-5"
    ANTHROPIC_SMART_MODEL: str = "claude-sonnet-4-5"
    ANTHROPIC_FALLBACK_MODELS: List[str] = [
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
    ]

    # ── Gemini models (tertiary fallback) ─────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_CHAT_MODEL: str = "gemini-2.0-flash"
    GEMINI_SMART_MODEL: str = "gemini-2.0-flash"
    GEMINI_FALLBACK_MODELS: List[str] = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    # ── Vector DB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = str(Path(__file__).parent.parent / "chroma_db")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Token limits ──────────────────────────────────────────────────────────
    MAX_TOKENS_CAREER_ADVICE: int = 2000
    MAX_TOKENS_ROADMAP: int = 6000
    MAX_TOKENS_CHAT: int = 1024
    MAX_TOKENS_INSIGHTS: int = 1500

    # ── Storage directories ───────────────────────────────────────────────────
    FEEDBACK_STORE_DIR: str = str(
        Path(__file__).parent.parent.parent / "tmp" / "career_genie_feedback"
    )
    LTR_STORE_DIR: str = str(
        Path(__file__).parent.parent.parent / "tmp" / "career_genie_ltr"
    )
    PROGRESS_STORE_DIR: str = str(
        Path(__file__).parent.parent.parent / "tmp" / "career_genie_progress"
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    #: Set False in production and populate CORS_ORIGINS instead.
    CORS_ALLOW_ALL: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    NGROK_URL: str = ""

    # ── Upload security ───────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx"]

    # ── Job search defaults ───────────────────────────────────────────────────
    DEFAULT_NUM_JOBS: int = 50
    DEFAULT_TOP_K: int = 10

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    #: Must be True in production — enforced by validate_config().
    RATE_LIMIT_ENABLED: bool = False

    # ── Cache TTL ─────────────────────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 3600   # 1 hour

    # ── AI pipeline ───────────────────────────────────────────────────────────
    #: Maximum characters allowed in user-supplied content before truncation.
    MAX_USER_CONTENT_LENGTH: int = 8000
    #: How many times the LLM router retries before raising LLMUnavailableError.
    LLM_MAX_RETRIES: int = 3
    #: Seconds to wait between retry attempts.
    LLM_RETRY_DELAY: float = 1.0

    # ── Tech skills master list ───────────────────────────────────────────────
    TECH_SKILLS: List[str] = [
        # Languages
        "python", "java", "javascript", "typescript", "c++", "c#",
        "ruby", "go", "rust", "php", "swift", "kotlin", "scala", "r",
        # Frontend
        "react", "angular", "vue", "svelte", "html", "css", "sass",
        "tailwind", "bootstrap", "webpack", "vite",
        # Backend / frameworks
        "node.js", "nodejs", "express", "django", "flask", "fastapi",
        "spring boot", "asp.net", "rails", "laravel", "nest.js",
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "dynamodb",
        "oracle", "cassandra", "elasticsearch", "firebase",
        # Cloud / DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
        "terraform", "ansible", "ci/cd", "github actions", "gitlab ci",
        # AI / ML
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "pandas", "numpy", "matplotlib", "nlp",
        "computer vision", "data analysis", "statistics",
        # General tools
        "git", "jira", "confluence", "linux", "bash", "agile", "scrum",
        "rest api", "restful", "graphql", "microservices", "system design",
        "testing", "jest", "pytest", "selenium", "unit testing",
        # Manufacturing / embedded (automotive / EV roles)
        "bms", "can bus", "plc", "cnc", "scada", "iatf",
        "lean manufacturing", "solidworks", "autocad", "catia",
        "embedded c", "microcontroller", "arduino", "stm32",
        "iot", "industry 4.0", "hydraulics", "pneumatics",
    ]

    # ── Pydantic model config ─────────────────────────────────────────────────
    if _PYDANTIC_V2:
        model_config = SettingsConfigDict(  # type: ignore[misc]
            env_file=str(_ENV_PATH),
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    else:
        class Config:                       # type: ignore[misc]
            env_file = str(_ENV_PATH)
            case_sensitive = False
            extra = "ignore"

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def effective_serpapi_key(self) -> Optional[str]:
        """Return SERPAPI_KEY, falling back to SEARCHAPI_KEY."""
        return self.SERPAPI_KEY or self.SEARCHAPI_KEY

    @property
    def is_production(self) -> bool:
        return self.DEPLOYMENT_MODE.lower() == "production"

    @property
    def cors_origins(self) -> List[str]:
        """Effective CORS origin list, incorporating NGROK_URL when set."""
        if self.CORS_ALLOW_ALL:
            return ["*"]
        origins = list(self.CORS_ORIGINS)
        if self.NGROK_URL:
            origins.append(self.NGROK_URL)
        return origins

    @property
    def max_upload_bytes(self) -> int:
        """Upload size limit in bytes (computed from MAX_UPLOAD_SIZE_MB)."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Startup helpers ───────────────────────────────────────────────────────

    def validate_config(self) -> List[str]:
        """
        Return a list of *non-fatal* configuration warnings.

        Call at application startup and log each warning.  These are warnings,
        not errors — the server will still start, but some features may degrade.

        Example::

            for w in settings.validate_config():
                logger.warning("Config: %s", w)
        """
        warnings: List[str] = []

        if not self.effective_serpapi_key:
            warnings.append(
                "SERPAPI_KEY / SEARCHAPI_KEY not set — job search will use mock data"
            )
        if not self.GROQ_API_KEY and not self.ANTHROPIC_API_KEY:
            warnings.append(
                "No cloud LLM API keys configured — Ollama must be running locally"
            )
        if self.is_production and self.CORS_ALLOW_ALL:
            warnings.append(
                "CORS_ALLOW_ALL=True in production — restrict CORS_ORIGINS for security"
            )
        if self.is_production and not self.RATE_LIMIT_ENABLED:
            warnings.append(
                "RATE_LIMIT_ENABLED=False in production — enable to prevent abuse"
            )

        return warnings

    def ensure_directories(self) -> None:
        """
        Create all required runtime directories (idempotent).

        Call once at startup so services never fail on missing directories.
        """
        for path_str in (
            self.FEEDBACK_STORE_DIR,
            self.LTR_STORE_DIR,
            self.PROGRESS_STORE_DIR,
            self.CHROMA_PERSIST_DIR,
        ):
            Path(path_str).mkdir(parents=True, exist_ok=True)


# ── Singleton ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()


# Convenience alias — ``from backend.core.config import settings``
settings = get_settings()
