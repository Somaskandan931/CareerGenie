# Career Genie — AI-Powered Career Intelligence Platform

> From resume to offer: semantic job matching, ATS scoring, mock interviews, LangChain-powered resume rewriting, and a LangGraph career analysis pipeline — all in one system, running locally with Ollama.

---

## Problem Statement

Job seekers today face a fragmented landscape: one tool shows job listings, another grades your resume, and a third offers generic interview tips — but none of these systems talk to each other or adapt to the individual. A fresh graduate in Tamil Nadu applying for a software role has no unified way to understand their skill gaps, find semantically relevant jobs, prepare for interviews, and track their progress toward an offer.

Career Genie solves this by connecting every stage of the job search into a single coherent pipeline. It analyses the user's actual resume, identifies skill gaps relative to their target role, retrieves semantically matched live job listings, scores and rewrites the resume for ATS compatibility, generates a week-by-week learning roadmap, conducts mock interviews with scored feedback, and tracks progress — all personalised to the user and validated for output confidence before anything is shown.

---

## Features

| Feature | What it does |
|---|---|
| **Resume Parsing** | Extracts plain text from uploaded PDF or DOCX resumes using pdfplumber and python-docx |
| **ATS Scorer** | Scores a resume against a target role or job description; returns overall score, keyword score, format score, missing/found keywords, section feedback, bullet quality, and improvement suggestions |
| **Resume Rewriter** | LangChain PromptTemplate + LLMChain rewrite pipeline — action verbs, quantified achievements, ATS-friendly formatting; falls back to direct LLM call if LangChain is unavailable |
| **Semantic Job Matching** | Embeds the resume and job listings using Ollama (all-minilm); retrieves the top-k matches via ChromaDB cosine similarity with a freshness boost for recent postings |
| **Adaptive Scoring** | Computes a weighted match score (semantic 35%, skill overlap 45%, title alignment 20%) that adapts per user over time based on recorded feedback signals using EMA |
| **Learning-to-Rank** | Re-ranks job matches using a pairwise BPR SGD model trained on the user's revealed job preferences; auto-retrains every 20 new pairs; NDCG@5 evaluated after each run |
| **Job Intelligence** | Fetches live job listings from Google Jobs via SerpAPI; filters and quality-scores postings (0–10) based on red flags, description length, company legitimacy, and apply link presence |
| **Employer Job Posting** | Employers can post jobs directly into the ChromaDB vector store via the `/jobs/post` endpoint; postings appear on the candidate board immediately and are matched semantically like any other listing |
| **AI Job Coach** | Stateless conversational career coach ("Genie") backed by Ollama with cloud fallbacks; accepts full conversation history and resume context per request |
| **Mock Interviews** | Generates technical, behavioural, and HR question banks with difficulty levels and ideal answer key points; evaluates candidate answers 0–10 with strengths, improvements, and a sample answer |
| **Live Interview Sessions** | WebRTC-based real-time mock interview sessions with WebSocket signalling; VideoPanel and LiveFeedback components deliver in-session feedback |
| **HR Recruiter Simulation** | Simulates a full HR panel evaluation: hire verdict, dimension scores, green/red flags, interview questions, salary bracket estimate, and internal recruiter notes |
| **LangGraph Deep Analysis** | 4-node StateGraph pipeline: `parse_resume → gap_analysis → generate_roadmap → suggest_projects`; each node receives the full accumulated state from all previous nodes; falls back to sequential execution if langgraph is not installed |
| **Learning Roadmap** | Generates a phased, week-by-week learning plan from skill gaps with verified resource URLs injected from an internal database |
| **Portfolio Projects** | Suggests real-world portfolio projects tailored to skill gaps with tech stack, learning outcomes, and recruiter impact statement |
| **Multi-Agent Debate** | Runs a Propose → Critique → Synthesise → Reflect loop using five typed agents to stress-test career recommendations before surfacing them |
| **Expert Mentors** | Browse and book sessions with industry professionals; mentor profiles are matched to the user's skill gaps |
| **Market Insights** | Fetches Google Trends data for up to 10 skill keywords with 6-hour in-memory cache; generates LLM analysis of market demand and salary trends |
| **Progress Tracker** | Tracks DSA problems, roadmap tasks, portfolio projects, and interview pipeline with streak, skill velocity, and retention risk metrics per user |
| **TN SkillBridge Analytics** | NSQF-aligned skill taxonomy for Tamil Nadu's automotive sector; batch analytics for institutions tracking student/worker readiness across 7 job roles |
| **Uncertainty Handler** | Validates every system output before returning it; assigns confidence tiers (high / medium / low / unreliable) and flags or retries low-confidence outputs |
| **Feedback Engine** | Records 9 signal types (apply click, offer received, dismiss, etc.) with signed rewards; updates adaptive scoring weights per user via EMA |

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Tailwind CSS | Styling |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI (Python 3.10+) | REST API framework |
| LangChain | Resume rewriter pipeline (PromptTemplate + LLMChain) |
| LangGraph | 4-node career analysis StateGraph |
| Ollama (llama3.2:3b) | Primary local LLM |
| Ollama (all-minilm) | Primary local embeddings (384-dim) |
| Groq (Llama 3.3 70B) | LLM cloud fallback 1 |
| Anthropic Claude | LLM cloud fallback 2 |
| Gemini | LLM cloud fallback 3 |
| Sentence Transformers (all-MiniLM-L6-v2) | Embeddings fallback |
| ChromaDB | Persistent vector database for job retrieval |
| SerpAPI (Google Jobs engine) | Live job listing retrieval |
| pytrends | Google Trends data for market insights |
| pdfplumber | PDF resume parsing |
| python-docx | DOCX resume parsing |
| Custom BPR SGD | Pairwise learning-to-rank model (pure Python) |
| Per-user JSON files | User progress and feedback persistence |

---

## Project Structure

```
career-genie/
├── backend/
│   ├── main.py                          # FastAPI app, all route definitions
│   ├── config.py                        # Settings, tech skills list, environment vars
│   ├── models.py                        # All Pydantic request/response models (single source of truth)
│   ├── requirements.txt                 # Python dependencies
│   ├── routes/
│   │   └── interview_live.py            # WebRTC live interview WebSocket endpoints
│   └── services/
│       ├── llm.py                       # LLM provider waterfall (Ollama → Groq → Anthropic → Gemini)
│       ├── resume_parser.py             # PDF/DOCX text extraction
│       ├── resume_rewriter.py           # LangChain PromptTemplate + LLMChain ATS rewriter
│       ├── langgraph_career_flow.py     # 4-node LangGraph career analysis pipeline
│       ├── ats_scorer.py                # ATS scoring engine with JSON parsing and fallback
│       ├── matcher.py                   # Job matching pipeline (RAG + adaptive scoring + LTR)
│       ├── vector_store.py              # ChromaDB wrapper with Ollama embeddings and freshness boost
│       ├── enhanced_skill_extractor.py  # Skill extraction with proficiency and experience detection
│       ├── job_scraper.py               # SerpAPI job fetcher with MD5-keyed in-memory cache
│       ├── job_filter.py                # Quality scoring and scam detection for job listings
│       ├── job_coach.py                 # Conversational career coach backed by Ollama
│       ├── interview_coach.py           # Mock interview question generation and answer evaluation
│       ├── career_advisor.py            # Career plan generation from resume + cross-agent context
│       ├── market_insights.py           # Google Trends + LLM market analysis with 6hr cache
│       ├── roadmap_generator.py         # Week-by-week phased learning roadmap generator
│       ├── project_generator.py         # Portfolio project suggestion engine
│       ├── feedback_engine.py           # Signal recording, EMA weight updates, personalised scoring
│       ├── learning_to_rank.py          # BPR SGD pairwise ranking model with NDCG evaluation
│       ├── agent_orchestrator.py        # Five-agent orchestration layer with shared memory bus
│       ├── agent_debate.py              # Multi-agent propose-critique-synthesise debate loop
│       ├── confidence.py                # Score-based and entropy-based confidence estimation
│       ├── consistency.py               # Self-consistency checker for multi-agent outputs
│       ├── scoring.py                   # Cosine relevance scoring and voting for debate system
│       ├── retriever.py                 # RAG retriever — ChromaDB wrapper with structured context builder
│       ├── skill_tool.py                # Agent-facing skill extraction tool interface
│       ├── job_tool.py                  # Agent-facing job search tool interface
│       ├── state_manager.py             # Session-persistent state manager across requests
│       ├── ollama_embedder.py           # Concurrent-batch Ollama embedder (drop-in for SentenceTransformer)
│       ├── ollama_service.py            # Ollama availability check and model management
│       ├── mentor_service.py            # Expert mentor matching and session booking
│       ├── uncertainty_handler.py       # Output confidence scoring, validation, and consistency checks
│       ├── progress_tracker.py          # Per-user progress tracking across all modules
│       ├── progress_store.py            # JSON persistence for progress data
│       ├── live_session.py              # Live interview session state and signalling
│       └── tn_automotive_taxonomy.py    # NSQF-aligned TN sector skill taxonomy and batch analytics
├── src/
│   ├── App.js                           # Root component and navigation
│   ├── config.js                        # API base URL config
│   └── components/
│       ├── HomePage.jsx                 # Dashboard landing page with feature cards and stats
│       ├── JobPost.jsx                  # Employer job posting form
│       ├── JobMatches.js                # Job match results with LTR re-ranking display
│       ├── JobSearch.js                 # Job search input and filter controls
│       ├── ResumeAnalyzer.js            # ATS scorer + HR recruiter simulation UI
│       ├── ResumeRewriter.js            # LangChain resume rewriter UI
│       ├── InterviewCoach.js            # Mock interview UI with live session support
│       ├── LiveFeedback.jsx             # Real-time answer feedback display (used by InterviewCoach)
│       ├── VideoPanel.jsx               # WebRTC video panel for live mock interviews
│       ├── Roadmapview.js               # Learning roadmap display and progress tracking
│       ├── ProjectSuggestions.js        # Portfolio project suggestion UI
│       ├── ProgressDashboard.js         # Progress dashboard with streak and velocity metrics
│       ├── JobCoachChat.js              # Conversational job coach chat UI
│       ├── MarketInsights.js            # Trend charts and market analysis UI
│       ├── MentorSearch.js              # Expert mentor discovery and booking UI
│       ├── SkillAssessmentDashboard.js  # Skill gap visualisation
│       └── TNAnalyticsDashboard.js      # TN SkillBridge institution analytics UI
└── test_ollama_setup.py                 # Ollama connectivity and model availability test
```

---

## Installation & Setup

### Prerequisites

**1. Install Ollama** (required — primary LLM and embedding provider)
```bash
# Download from https://ollama.com/download and install
# Then pull the required models:
ollama pull llama3.2:3b
ollama pull all-minilm
```

**2. Python 3.10+** and **Node.js 18+** must be installed.

**3. Get a SerpAPI key** at https://serpapi.com (required for job matching).

---

### Backend Setup

```bash
# 1. Create and activate virtual environment
cd CareerGenie
python -m venv venv
venv\Scripts\activate

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Install LangChain + LangGraph
pip install langchain langchain-community langchain-groq langgraph

# 4. Create environment file
cp .env.example .env
# Edit .env and set at minimum:
# SERPAPI_KEY=your_serpapi_key_here

# 5. Start Ollama in a separate terminal
ollama serve

# 6. Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### Frontend Setup

```bash
cd frontend/resume-frontend
npm install
npm start
# App runs at http://localhost:3000
```

---

### Verify Everything Works

```bash
python test_ollama_setup.py
curl http://localhost:8000/
```

---

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SERPAPI_KEY` | **Yes** | — | SerpAPI key for Google Jobs |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama API host |
| `OLLAMA_LLM_MODEL` | No | `llama3.2:3b` | Ollama LLM model |
| `OLLAMA_EMBEDDING_MODEL` | No | `all-minilm` | Ollama embedding model |
| `GROQ_API_KEY` | No | — | Groq fallback (if Ollama unavailable) |
| `ANTHROPIC_API_KEY` | No | — | Anthropic fallback |
| `GEMINI_API_KEY` | No | — | Gemini fallback |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |
| `FEEDBACK_STORE_DIR` | No | `/tmp/career_genie_feedback` | Feedback engine store |
| `LTR_STORE_DIR` | No | `/tmp/career_genie_ltr` | LTR model store |

---

## How It Works

### 1. Resume Upload & Parsing
User uploads a PDF or DOCX → `resume_parser.py` extracts plain text using pdfplumber or python-docx → uncertainty_handler validates the parse → validated text is passed to all downstream services.

### 2. ATS Scoring
Resume text + target role (+ optional job description) → `ats_scorer.py` sends a structured prompt to the LLM → receives JSON with overall score, keyword score, format score, missing/found keywords, per-section feedback, bullet quality, and improvement suggestions → JSON is cleaned, parsed with fallback strategies, and validated.

### 3. Resume Rewriting (LangChain)
Resume text + target role + tone → `resume_rewriter.py` builds a `PromptTemplate + LLMChain` using Ollama (primary) or Groq (fallback) → generates an ATS-optimised resume → also generates before/after comparisons and a changes summary.

### 4. Semantic Job Matching
Resume text → Ollama (all-minilm) embeds it → ChromaDB retrieves top-k candidate jobs with freshness boost → `enhanced_skill_extractor` extracts skills → candidates are scored with semantic + skill overlap + title alignment → personalised scoring + LTR re-ranking → validated output.

### 5. Employer Job Posting
Employers post a job via `POST /jobs/post` → it is indexed into ChromaDB immediately and becomes available through semantic matching.

### 6. LangGraph Deep Analysis
`POST /career/deep-analysis` builds a `StateGraph` with 4 nodes: `parse_resume → gap_analysis → generate_roadmap → suggest_projects`.

### 7. Learning-to-Rank Adaptation
Feedback signals (apply, save, dismiss, offer) update EMA scoring weights and retrain a lightweight pairwise BPR SGD model periodically.

### 8. Multi-Agent Debate
`full_analysis` runs multiple agents in a Propose → Critique → Synthesise → Reflect loop to reduce hallucinations and increase confidence.

### 9. Mock Interview & HR Panel
`interview_coach.py` generates questions and evaluates answers 0–10. HR simulation generates a structured panel (verdict, dimensions, flags, questions, salary bracket).

### 10. Learning Roadmap Generation
Skill gaps + target role → `roadmap_generator.py` generates week-by-week learning plan and injects verified resource URLs.

---

## API Reference (Key Endpoints)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/resume/upload` | Upload PDF or DOCX, returns extracted text |
| `POST` | `/resume/analyze` | ATS score + HR recruiter simulation |
| `POST` | `/resume/rewrite` | LangChain-powered ATS resume rewrite |
| `POST` | `/jobs/match` | Semantic job matching with LTR re-ranking |
| `POST` | `/jobs/post` | Employer job posting into vector store |
| `GET` | `/jobs/posted` | List all employer-posted jobs |
| `POST` | `/career/deep-analysis` | LangGraph 4-node career analysis pipeline |
| `POST` | `/career/advice` | Career advice with skill gap analysis |
| `POST` | `/roadmap/generate` | Week-by-week learning roadmap |
| `POST` | `/projects/suggest` | Portfolio project suggestions |
| `POST` | `/interview/questions` | Generate interview question bank |
| `POST` | `/interview/evaluate` | Evaluate candidate answer 0–10 |
| `POST` | `/chat` | Job coach conversational endpoint |
| `POST` | `/agents/run` | Multi-agent orchestrator |
| `POST` | `/debate/run` | Multi-agent debate loop |
| `POST` | `/mentor/search` | Search expert mentors |
| `POST` | `/mentor/book` | Book mentor session |
| `GET` | `/market/insights` | Google Trends + LLM market analysis |
| `POST` | `/feedback/record` | Record user feedback signal |
| `POST` | `/ranking/preference` | Record pairwise job preference for LTR |

---

## Scalability

1. Stateless backend + scalable vector retrieval via ChromaDB.
2. LLM provider waterfall (Ollama → Groq → Anthropic → Gemini) to absorb load spikes.
3. Lightweight LTR re-ranking with measurable NDCG@5 evaluation.
4. LangGraph can be extended with conditional edges without changing node contracts.

---

## Feasibility

Built and tested end-to-end on a standard laptop with Ollama. Minimal required external dependency is SerpAPI for live jobs.

---

## Novelty

Most career tools are point solutions; Career Genie combines semantic retrieval, adaptive scoring, deep analysis via LangGraph, multi-agent debate, and confidence-gated output validation.

---

## Ethical Use & Disclaimer

Career Genie uses AI-generated content for resume analysis, HR simulation, interview evaluation, and career advice. All outputs are informational only and do not constitute professional career, legal, or financial advice.

---

## License

MIT License — see LICENSE file for details.

---

## Author

Built for Origin 2026.

**Team Name:** Neon Genesis
**Contact:** somaskandan931@gmail.com
**GitHub:** [Somaskandan931](https://github.com/Somaskandan931)

