
<div align="center">

```
 ██████╗ █████╗ ██████╗ ███████╗███████╗██████╗      ██████╗ ███████╗███╗   ██╗██╗███████╗
██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗    ██╔════╝ ██╔════╝████╗  ██║██║██╔════╝
██║     ███████║██████╔╝█████╗  █████╗  ██████╔╝    ██║  ███╗█████╗  ██╔██╗ ██║██║█████╗  
██║     ██╔══██║██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗    ██║   ██║██╔══╝  ██║╚██╗██║██║██╔══╝  
╚██████╗██║  ██║██║  ██║███████╗███████╗██║  ██║    ╚██████╔╝███████╗██║ ╚████║██║███████╗
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚═╝  ╚════╝╚═╝╚══════╝
```

**AI-powered career intelligence platform for resume optimisation, semantic job matching, interview preparation, and adaptive career guidance.**

Semantic job matching · ATS scoring · LangChain resume rewriting · LangGraph career analysis · Mock interviews · Adaptive personalisation · Runs locally with Ollama.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![LangChain](https://img.shields.io/badge/LangChain-latest-1C3C3C?style=flat-square)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--db-FF6719?style=flat-square)](https://trychroma.com)
[![Ollama](https://img.shields.io/badge/Ollama-local--LLM-black?style=flat-square)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Built for Origin 2026](https://img.shields.io/badge/Built%20for-Origin%202026-6C63FF?style=flat-square)](https://github.com/Somaskandan931)

</div>

---

## The Problem

Modern job seekers use disconnected tools for resume optimisation, job discovery, interview preparation, and skill development. These systems rarely share context with one another, leading to fragmented workflows and generic recommendations.

A candidate may improve their resume in one platform, search for jobs in another, and practise interviews elsewhere — without any system understanding their complete career profile, evolving strengths, or long-term goals.

Career Genie addresses this by creating a unified AI-driven career pipeline that connects resume analysis, semantic job retrieval, adaptive recommendations, interview coaching, and personalised learning into a single continuously improving system.

---

## What It Does

```text
Resume Upload
      ↓
ATS Analysis + Skill Extraction
      ↓
Semantic Job Matching
      ↓
Gap Analysis
      ↓
Resume Rewriting + Portfolio Suggestions
      ↓
Learning Roadmap + Interview Preparation
      ↓
Adaptive Feedback Loop + Progress Tracking
```

---

## Feature Overview

### Core Intelligence

| Feature | Description |
|---|---|
| **Resume Parser** | Extracts structured text from PDF and DOCX using pdfplumber and python-docx |
| **ATS Scorer** | Scores against a role or JD; returns overall score, keyword score, format score, missing keywords, section feedback, bullet quality, and improvement suggestions — with 4-strategy JSON fallback parsing |
| **Resume Rewriter** | LangChain `PromptTemplate + LLMChain` pipeline — action verbs, quantified achievements, ATS-friendly formatting; generates before/after bullet comparisons and a changes summary |
| **LangGraph Deep Analysis** | 4-node `StateGraph`: `parse_resume → gap_analysis → generate_roadmap → suggest_projects`; each node receives full accumulated state from all previous nodes |

### Job Intelligence

| Feature | Description |
|---|---|
| **Semantic Job Matching** | Embeds resume via Ollama (all-minilm); retrieves top-k jobs from ChromaDB with cosine similarity and a freshness boost for recent postings |
| **Adaptive Scoring** | Weighted match score (semantic 35%, skill overlap 45%, title alignment 20%) that adapts per user via EMA on recorded feedback signals |
| **Learning-to-Rank** | Pairwise BPR SGD model (12 features) trained on revealed job preferences; auto-retrains every 20 pairs; NDCG@5 evaluated after each run |
| **Job Quality Filter** | Scores listings 0–10 based on red-flag phrases, description length, company legitimacy, and apply link presence; detects scam patterns |
| **Live Job Listings** | Fetches from Google Jobs via SerpAPI; MD5-keyed 5-minute in-memory cache reduces redundant API calls |
| **Employer Job Posting** | Employers post directly into ChromaDB via `/jobs/post`; listings appear immediately and match semantically like any other posting |

### AI Coaching

| Feature | Description |
|---|---|
| **AI Job Coach** | Stateless conversational coach ("Genie") backed by Ollama with cloud fallbacks; full conversation history and resume context per request |
| **Mock Interviews** | Generates technical, behavioural, and HR question banks with difficulty levels and ideal answer key points |
| **Answer Evaluation** | Scores candidate answers 0–10 with strengths, improvements, and a sample ideal answer |
| **Live Interview Sessions** | WebRTC-based real-time mock interviews with WebSocket signalling; VideoPanel and LiveFeedback components deliver in-session coaching |
| **HR Recruiter Simulation** | Simulates a full panel: hire verdict, 5 dimension scores, green/red flags, interview questions, salary bracket estimate, internal recruiter notes |

### Advanced Systems

| Feature | Description |
|---|---|
| **Multi-Agent Debate** | Propose → Critique → Synthesise → Reflect loop using five typed agents; improves reasoning quality and surfaces trade-offs |
| **Confidence-Gated Validation** | Every output passes through a typed validator with 4 confidence tiers (high / medium / low / unreliable); low-confidence outputs trigger retries or flags |
| **Learning Roadmap** | Week-by-week phased learning plan from skill gaps with verified resource URLs injected from an internal database |
| **Portfolio Projects** | Tailored real-world project suggestions with tech stack, learning outcomes, and recruiter impact statement |
| **Market Insights** | Google Trends data for up to 10 skill keywords with 6-hour cache; LLM analysis of market demand and salary trends |
| **Progress Tracker** | DSA problems, roadmap tasks, portfolio projects, and interview pipeline with streak, skill velocity, and retention risk metrics per user |
| **Expert Mentors** | Browse and book sessions with industry professionals matched to your skill gaps |

---

## Tech Stack

**Backend**

| Technology | Role |
|---|---|
| FastAPI (Python 3.10+) | REST API framework |
| LangChain | Resume rewriter pipeline (PromptTemplate + LLMChain) |
| LangGraph | 4-node career analysis StateGraph |
| ChromaDB | Persistent vector database for job retrieval |
| Ollama `llama3.2:3b` | Primary local LLM |
| Ollama `all-minilm` | Primary local embeddings (384-dim) |
| Groq → Anthropic → Gemini | LLM cloud fallback waterfall |
| Sentence Transformers | Embeddings fallback |
| SerpAPI | Live job listing retrieval (Google Jobs engine) |
| pytrends | Google Trends data |
| pdfplumber + python-docx | Resume parsing |
| Custom BPR SGD | Pairwise learning-to-rank (pure Python) |

**Frontend**

| Technology | Role |
|---|---|
| React 18 | UI framework |
| Tailwind CSS | Styling |

---

## System Architecture

Career Genie follows a modular AI-service architecture built around retrieval, orchestration, and adaptive feedback systems.

### Core Pipeline

```text
Frontend (React)
       ↓
FastAPI Gateway
       ↓
Resume Processing Layer
       ├── Resume Parser
       ├── ATS Scorer
       ├── Skill Extractor
       └── Resume Rewriter
       ↓
AI Intelligence Layer
       ├── LangChain Pipelines
       ├── LangGraph Career Flow
       ├── Multi-Agent Orchestrator
       └── Interview Evaluation Engine
       ↓
Retrieval + Ranking Layer
       ├── ChromaDB Vector Store
       ├── Semantic Job Matcher
       ├── Learning-to-Rank Engine
       └── Feedback Adaptation System
       ↓
Output Services
       ├── Job Recommendations
       ├── Learning Roadmaps
       ├── Portfolio Projects
       ├── Interview Coaching
       └── Progress Analytics
```

### Design Characteristics

* Modular service-oriented backend
* Local-first LLM inference using Ollama
* Retrieval-augmented semantic job search
* Adaptive ranking using user feedback
* Extensible LangGraph workflow pipelines
* Cloud fallback support for reliability
* Vector-based retrieval with persistent embeddings

---

## Key Innovations

### Adaptive Job Matching

Career Genie combines semantic similarity, skill overlap analysis, and personalised ranking signals to improve recommendations over time using recorded user feedback.

### LangGraph-Based Career Workflow

The platform uses a structured multi-stage LangGraph pipeline where each stage builds upon accumulated analysis state, enabling more contextual recommendations.

### Multi-Agent Recommendation System

Instead of relying on a single generation step, the platform supports proposer–critic style reasoning workflows for more balanced career guidance.

### Local-First AI Architecture

The system is designed to run primarily on Ollama, reducing dependence on cloud APIs and improving privacy for users and institutions.

### Unified Career Pipeline

Resume analysis, job matching, interview preparation, roadmap generation, and progress tracking are integrated into a single workflow rather than isolated tools.

---

## Project Structure

```
career-genie/
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── core/
│   │   ├── config.py                    # Settings and environment variables
│   │   ├── prompts.py                   # All LLM prompt templates
│   │   ├── exceptions.py                # Typed exception hierarchy
│   │   ├── logging.py                   # Structured logging setup
│   │   └── ai_pipeline.py              # Core pipeline orchestration
│   ├── api/
│   │   ├── routes/
│   │   │   ├── resume.py               # /resume/* endpoints
│   │   │   ├── jobs.py                 # /jobs/* endpoints
│   │   │   ├── coach.py                # /chat endpoint
│   │   │   ├── roadmap.py              # /roadmap/* endpoints
│   │   │   ├── insights.py             # /market/* endpoints
│   │   │   ├── progress.py             # /progress/* endpoints
│   │   │   ├── mentor.py               # /mentor/* endpoints
│   │   │   ├── admin.py                # /admin/* endpoints
│   │   │   └── auth.py                 # Authentication routes
│   │   └── middleware/
│   │       ├── rate_limit.py           # Rate limiting middleware
│   │       ├── trace.py                # Request tracing
│   │       └── request_middleware.py   # General request handling
│   └── services/
│       ├── llm.py                       # LLM provider waterfall
│       ├── resume_parser.py             # PDF/DOCX extraction
│       ├── resume_rewriter.py           # LangChain ATS rewriter
│       ├── langgraph_career_flow.py     # 4-node LangGraph pipeline
│       ├── ats_scorer.py                # ATS scoring engine
│       ├── matcher.py                   # Job matching (RAG + LTR)
│       ├── vector_store.py              # ChromaDB + Ollama embeddings
│       ├── enhanced_skill_extractor.py  # Skill extraction with proficiency
│       ├── job_scraper.py               # SerpAPI fetcher + cache
│       ├── job_filter.py                # Quality scoring + scam detection
│       ├── job_coach.py                 # Conversational career coach
│       ├── interview_coach.py           # Mock interview + evaluation
│       ├── career_advisor.py            # Career plan generation
│       ├── market_insights.py           # Trends + LLM analysis
│       ├── roadmap_generator.py         # Week-by-week roadmap
│       ├── project_generator.py         # Portfolio project suggestions
│       ├── feedback_engine.py           # Signal recording + EMA weights
│       ├── learning_to_rank.py          # BPR SGD ranking model
│       ├── agent_orchestrator.py        # Five-agent orchestration
│       ├── agent_debate.py              # Multi-agent debate loop
│       ├── uncertainty_handler.py       # Confidence validation
│       ├── progress_tracker.py          # Per-user progress tracking
│       ├── mentor_service.py            # Mentor matching + booking
│       ├── ollama_service.py            # Ollama model management
│       └── tn_automotive_taxonomy.py    # TN sector analytics
└── src/
    ├── App.js
    └── components/
        ├── HomePage.jsx
        ├── JobMatches.js
        ├── ResumeAnalyzer.js
        ├── ResumeRewriter.js
        ├── InterviewCoach.js
        ├── LiveFeedback.jsx
        ├── VideoPanel.jsx
        ├── Roadmapview.js
        ├── ProgressDashboard.js
        ├── JobCoachChat.js
        ├── MarketInsights.js
        ├── MentorSearch.js
        └── TNAnalyticsDashboard.js
```

---

## Installation & Setup

### Prerequisites

**1. Install Ollama** (required — primary LLM and embedding provider)

```bash
# Download from https://ollama.com/download then pull the required models
ollama pull llama3.2:3b
ollama pull all-minilm
```

**2. Python 3.10+** and **Node.js 18+**

**3. SerpAPI key** — free tier at https://serpapi.com (100 searches/month)

---

### Backend

```bash
# Clone and navigate to the project
git clone https://github.com/Somaskandan931/CareerGenie.git
cd CareerGenie

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
cd backend
pip install -r requirements.txt
pip install langchain langchain-community langchain-groq langgraph

# Configure environment
cp .env.example .env
# Edit .env — at minimum set SERPAPI_KEY=your_key_here

# Start Ollama in a separate terminal
ollama serve

# Start the backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend/resume-frontend
npm install
npm start
# Runs at http://localhost:3000
```

### Verify

```bash
python test_ollama_setup.py
curl http://localhost:8000/
```

---

## Deployment

### Local Deployment

Career Genie is designed to run fully locally using Ollama.

```bash
Frontend  → React + Tailwind
Backend   → FastAPI
LLM Layer → Ollama
Vector DB → ChromaDB
```

### Cloud-Compatible Deployment

The architecture also supports cloud deployment:

* Frontend → Netlify / Vercel
* Backend → Render / Railway / Azure
* Vector Storage → Persistent Docker volume
* LLM Fallbacks → Groq / Gemini / Anthropic

### Docker Support

The system is container-ready and can be deployed using Docker Compose with separate services for:

* frontend
* backend
* ollama
* chromadb

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SERPAPI_KEY` | **Yes** | — | SerpAPI key for Google Jobs |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama API host |
| `OLLAMA_LLM_MODEL` | No | `llama3.2:3b` | Ollama LLM model |
| `OLLAMA_EMBEDDING_MODEL` | No | `all-minilm` | Ollama embedding model |
| `GROQ_API_KEY` | No | — | Groq fallback |
| `ANTHROPIC_API_KEY` | No | — | Anthropic fallback |
| `GEMINI_API_KEY` | No | — | Gemini fallback |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |
| `FEEDBACK_STORE_DIR` | No | `/tmp/career_genie_feedback` | Feedback engine store |
| `LTR_STORE_DIR` | No | `/tmp/career_genie_ltr` | LTR model store |

> **Minimum viable setup:** `SERPAPI_KEY` + Ollama running. Everything else is optional.

---

## API Reference

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

Full interactive docs available at `http://localhost:8000/docs` when the server is running.

---

## How It Works

### Semantic Job Matching
Your resume is embedded via Ollama (`all-minilm`) and queried against ChromaDB using cosine similarity. Candidate jobs are scored with a weighted blend: **semantic similarity 35% + skill overlap 45% + title alignment 20%**. A freshness boost favours recent postings at query time without changing the index. Results are then re-ranked by a pairwise BPR SGD model trained on your own revealed preferences.

### LangChain Resume Rewriter
A `PromptTemplate` with three input variables (`resume_text`, `target_role`, `tone`) is bound to an `LLMChain`. LLM priority is Ollama → Groq → direct LLM fallback. A second call generates before/after bullet comparisons and a quantified changes summary (action verbs added, metrics inserted, word count delta).

### LangGraph Career Pipeline
`CareerState` is a TypedDict that flows through all four nodes:
1. **`parse_resume`** — extracts structured fields
2. **`gap_analysis`** — identifies missing skills relative to the target role
3. **`generate_roadmap`** — week-by-week plan grounded in gap output
4. **`suggest_projects`** — portfolio projects grounded in both gaps and roadmap

Each node receives the full accumulated state. The graph is built lazily at request time.

### Multi-Agent Debate
Three independent proposers generate career recommendations. A critic agent attacks each. A synthesiser produces a final output from the surviving arguments. A reflector checks for internal consistency. The approach improves reasoning quality and helps surface trade-offs.

### Confidence-Gated Output
Every module output passes through a typed validator before being returned. Four tiers: **high / medium / low / unreliable**. Low-confidence outputs trigger retries or explicit flags before being shown to users.

### Adaptive Personalisation Loop
Feedback signals (apply click, save, dismiss, offer received, and 5 others) update per-user EMA scoring weights. Every 20 new pairwise preference signals, the BPR SGD ranking model retrains. Population weights (all users) blend 60/40 with per-user weights — new users get good rankings immediately.

---

## Screenshots

| Dashboard | Resume Analysis | Job Matching |
|---|---|---|
| Add screenshot | Add screenshot | Add screenshot |

| Mock Interview | Learning Roadmap | Progress Tracker |
|---|---|---|
| Add screenshot | Add screenshot | Add screenshot |

---

## Future Work

* Fine-tuned ranking models using larger interaction datasets
* Real-time collaborative mentor sessions
* Institution-level analytics dashboards
* Voice-based mock interview evaluation
* Resume version tracking and optimisation history
* Multi-language support for regional users
* Reinforcement-learning-based recommendation tuning

---

## Scalability

- **Stateless backend** — all state lives in ChromaDB, per-user JSON files, or the LTR store. Multiple instances can run behind a load balancer; swap JSON for Redis for atomic writes under concurrency.
- **Vector retrieval** — The retrieval layer is designed to support scalable semantic search using persistent vector embeddings and batched indexing.
- **LLM waterfall** — if Ollama is saturated under concurrent load, requests automatically cascade to Groq → Anthropic → Gemini.
- **LTR model** — the 12-feature linear BPR model trains on 200 preference pairs in under 100ms.
- **LangGraph** — the current 4-node linear graph extends to conditional branching (e.g. skip roadmap if gaps are empty) without touching node implementations.
- **Bottlenecks identified** — the debate system makes 6–10 LLM calls per `full_analysis`. Mitigation: stream responses, cache synthesis per resume hash, or parallelise proposers.
- **Docker-ready** — backend, ChromaDB, and Ollama run in separate containers. A `docker-compose.yml` with named volumes brings the full stack up in one command.

---

## Ethical Use & Disclaimer

Career Genie uses AI-generated content for resume analysis, HR simulation, interview evaluation, and career advice. All outputs are **informational only** and do not constitute professional career, legal, or financial advice.

**HR Recruiter Simulation** — The hire verdict, dimension scores, and recruiter notes are generated by a language model. They are not the opinion of any real recruiter or employer and should not be treated as a prediction of actual hiring outcomes.

**ATS Scoring** — Scores are approximations based on keyword and format heuristics. They do not reflect the behaviour of any specific company's ATS system.

**Job Matching** — Listings are retrieved from Google Jobs via SerpAPI. Career Genie does not verify the accuracy, legitimacy, or current availability of any listed position.

**Data privacy** — No resume data is sent to external services unless Ollama is unavailable, in which case the configured fallback (Groq, Anthropic, or Gemini) is used. Running fully on Ollama keeps all data local.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built for **Origin 2026** &nbsp;·&nbsp; Team **Neon Genesis**

[somaskandan931@gmail.com](mailto:somaskandan931@gmail.com) &nbsp;·&nbsp; [github.com/Somaskandan931](https://github.com/Somaskandan931)

</div>
