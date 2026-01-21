import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    # API Keys - Support both SERPAPI_KEY and SEARCHAPI_KEY
    SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Vector DB - Store in backend folder
    CHROMA_PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Job Search Defaults
    DEFAULT_NUM_JOBS = 50
    DEFAULT_TOP_K = 10

    # Claude Model - Updated to use correct model name
    CLAUDE_MODEL = "claude-sonnet-4-20250514"

    # Career Advisor Settings
    MAX_TOKENS_CAREER_ADVICE = 2000

    # Tech Skills for Career Advisor
    TECH_SKILLS = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby",
        "go", "rust", "php", "swift", "kotlin", "scala", "r",

        # Frontend
        "react", "angular", "vue", "svelte", "html", "css", "sass",
        "tailwind", "bootstrap", "webpack", "vite",

        # Backend
        "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring boot",
        "asp.net", "rails", "laravel", "nest.js",

        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "dynamodb",
        "oracle", "cassandra", "elasticsearch", "firebase",

        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
        "terraform", "ansible", "ci/cd", "github actions", "gitlab ci",

        # Data Science & AI
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "pandas", "numpy", "matplotlib", "nlp",
        "computer vision", "data analysis", "statistics",

        # Tools & Others
        "git", "jira", "confluence", "linux", "bash", "agile", "scrum",
        "rest api", "restful", "graphql", "microservices", "system design",
        "testing", "jest", "pytest", "selenium", "unit testing"
    ]

    @classmethod
    def validate(cls):
        """Validate required settings"""
        errors = []

        if not cls.SERPAPI_KEY:
            errors.append("SERPAPI_KEY or SEARCHAPI_KEY not set in .env")

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY not set in .env")

        return errors


settings = Settings()