# Career Genie — AI-Powered Career Intelligence Platform

> From resume to offer: semantic job matching, ATS scoring, mock interviews, and personalised learning roadmaps — all in one system, running locally with Ollama.

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
| **Resume Rewriter** | Rewrites resumes for ATS optimisation with a professional summary, action verbs, quantified achievements, and ATS-friendly formatting |
| **Semantic Job Matching** | Embeds the resume and job listings using Ollama (all-minilm); retrieves the top-k matches via ChromaDB cosine similarity with a freshness boost for recent postings |
| **Adaptive Scoring** | Computes a weighted match score (semantic 35%, skill overlap 45%, title alignment 20%) that adapts per user over time based on recorded feedback signals using EMA |
| **Learning-to-Rank** | Re-ranks job matches using a pairwise BPR SGD model trained on the user's revealed job preferences; auto-retrains every 20 new pairs; NDCG@5 evaluated after each run |
| **Job Intelligence** | Fetches live job listings from Google Jobs via SerpAPI; filters and quality-scores postings (0–10) based on red flags, description length, company legitimacy, and apply link presence |
| **AI Job Coach** | Stateless conversational career coach ("Genie") backed by Ollama with cloud fallbacks; accepts full conversation history and resume context per request |
| **Mock Interviews** | Generates technical, behavioural, and HR question banks with difficulty levels and ideal answer key points; evaluates candidate answers 0–10 with strengths, improvements, and a sample answer |
| **HR Recruiter Simulation** | Simulates a full HR panel evaluation: hire verdict, dimension scores, green/red flags, interview questions, salary bracket estimate, and internal recruiter notes |
| **Learning Roadmap** | Generates a phased, week-by-week learning plan from skill gaps with verified resource URLs injected from an internal database |
| **Portfolio Projects** | Suggests real-world portfolio projects tailored to skill gaps with tech stack, learning outcomes, and recruiter impact statement |
| **Multi-Agent Debate** | Runs a Propose → Critique → Synthesise → Reflect loop using five typed agents to stress-test career recommendations before surfacing them |
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
│   ├── main.py                      # FastAPI app, all route definitions
│   ├── config.py                    # Settings, tech skills list, environment vars
│   ├── requirements.txt             # Python dependencies
│   └── services/
│       ├── llm.py                   # LLM provider waterfall (Ollama → Groq → Anthropic → Gemini)
│       ├── resume_parser.py         # PDF/DOCX text extraction
│       ├── resume_rewriter.py       # ATS-optimised resume rewriting
│       ├── ats_scorer.py            # ATS scoring engine with JSON parsing and fallback
│       ├── matcher.py               # Job matching pipeline (RAG + adaptive scoring + LTR)
│       ├── vector_store.py          # ChromaDB wrapper with Ollama embeddings and freshness boost
│       ├── enhanced_skill_extractor.py  # Skill extraction with proficiency and experience detection
│       ├── job_scraper.py           # SerpAPI job fetcher with MD5-keyed in-memory cache
│       ├── job_filter.py            # Quality scoring and scam detection for job listings
│       ├── job_coach.py             # Conversational career coach backed by Ollama
│       ├── interview_coach.py       # Mock interview question generation and answer evaluation
│       ├── career_advisor.py        # Career plan generation from resume + cross-agent context
│       ├── market_insights.py       # Google Trends + LLM market analysis with 6hr cache
│       ├── roadmap_generator.py     # Week-by-week phased learning roadmap generator
│       ├── project_generator.py     # Portfolio project suggestion engine
│       ├── feedback_engine.py       # Signal recording, EMA weight updates, personalised scoring
│       ├── learning_to_rank.py      # BPR SGD pairwise ranking model with NDCG evaluation
│       ├── agent_orchestrator.py    # Five-agent orchestration layer with shared memory bus
│       ├── agent_debate.py          # Multi-agent propose-critique-synthesise debate loop
│       ├── uncertainty_handler.py   # Output confidence scoring, validation, and consistency checks
│       ├── progress_tracker.py      # Per-user progress tracking across all modules
│       ├── progress_store.py        # JSON persistence for progress data
│       ├── tn_automotive_taxonomy.py # NSQF-aligned TN sector skill taxonomy and batch analytics
│       ├── ollama_service.py        # Ollama availability check and model management
│       └── live_session.py          # Live interview session state management
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ResumeAnalyzer.js    # ATS scorer + HR recruiter simulation UI
│   │   │   ├── JobMatches.js        # Job match results with LTR re-ranking display
│   │   │   ├── InterviewCoach.js    # Mock interview UI
│   │   │   ├── Roadmap.js           # Learning roadmap display and progress tracking
│   │   │   ├── MarketInsights.js    # Trend charts and market analysis UI
│   │   │   └── Dashboard.js         # Progress dashboard with streak and velocity metrics
│   │   └── App.js                   # Root component and routing
│   ├── package.json
│   └── tailwind.config.js
├── data/
│   └── chroma/                      # ChromaDB persistent vector store
└── test_ollama_setup.py             # Ollama connectivity and model availability test
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

**3. Get a SerpAPI key** at [serpapi.com](https://serpapi.com) (required for job matching).

---

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/career-genie.git
cd career-genie

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

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
# In a new terminal, from the project root:
cd frontend
npm install
npm start
# App runs at http://localhost:3000
```

---

### Verify Everything Works

```bash
# Test Ollama models are available
python test_ollama_setup.py

# Test backend health
curl http://localhost:8000/

# Expected response:
# {"name":"Career Genie AI API","version":"3.0.0","status":"operational",...}
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
| `CHROMA_PERSIST_DIR` | No | `./data/chroma` | ChromaDB storage path |
| `FEEDBACK_STORE_DIR` | No | `/tmp/career_genie_feedback` | Feedback engine store |
| `LTR_STORE_DIR` | No | `/tmp/career_genie_ltr` | LTR model store |

---

## How It Works

### 1. Resume Upload & Parsing
User uploads a PDF or DOCX → `resume_parser.py` extracts plain text using pdfplumber or python-docx → `uncertainty_handler` validates the parse (word count, section detection, encoding artefacts) → validated text is passed to all downstream services.

### 2. ATS Scoring
Resume text + target role (+ optional job description) → `ats_scorer.py` sends a structured prompt to the LLM → receives JSON with overall score, keyword score, format score, missing/found keywords, per-section feedback, bullet quality, and improvement suggestions → JSON is cleaned, parsed with 4 fallback strategies (direct parse → close unclosed braces → fix quote issues → regex partial extraction), and validated before returning.

### 3. Semantic Job Matching
Resume text → Ollama (all-minilm) embeds it as a 384-dim vector → ChromaDB retrieves the top-k*2 candidate jobs by cosine distance with a freshness boost for recent postings → `enhanced_skill_extractor` extracts skills from the resume → each candidate is scored: `0.35 × semantic + 0.45 × skill_overlap + 0.20 × title_alignment` with a critical skill penalty of up to -15 pts → `feedback_engine.personalise_score()` adds a ±10 pt profile bonus for returning users → `ltr_engine.rank()` applies the BPR pairwise model for users with ≥10 preference pairs → `uncertainty_handler` validates the final list.

### 4. Learning-to-Rank Adaptation
When a user clicks apply, saves a job, dismisses, or receives an offer → `feedback_engine` records the signal with a signed reward → EMA updates the user's adaptive scoring weights (α=0.15) → when 20 new pairwise preferences accumulate, the BPR SGD model retrains on the user's history → future job rankings reflect their revealed preferences.

### 5. Multi-Agent Debate
On `full_analysis` goal → `agent_orchestrator` plans tasks across 5 typed agents (Resume, Job, Interview, Roadmap, Advisor) sharing a common `AgentMemory` bus → `agent_debate.py` runs: 3 proposers generate independent career plans → `CriticAgent` attacks each → convergence check (if avg confidence ≥ 0.75, stop early; else run round 2 with revised proposals) → `SynthesisAgent` merges the best elements → `ReflectionLayer` self-assesses; if confidence < 0.6 the `RetryController` triggers a replan.

### 6. Mock Interview & HR Panel
User selects role + interview type → `interview_coach.py` prompts the LLM for a question bank with difficulty levels, hints, and ideal answer key points → user answers → answer is evaluated 0–10 with strengths, improvements, and a sample better answer. For HR simulation → `_generate_hr_panel()` in `main.py` prompts the LLM for a full structured panel (hire verdict, 5 dimension scores, green/red flags, recruiter questions, salary bracket, internal notes) → JSON is cleaned and validated with defaults before rendering.

### 7. Learning Roadmap Generation
Skill gaps from resume analysis → `roadmap_generator.py` sends gaps + target role + duration to the LLM → receives a week-by-week phased JSON plan → post-processes to replace null resource URLs with verified fallbacks from the internal `RELIABLE_RESOURCES` database → rendered as an interactive roadmap with progress tracking.

---

## Scalability

**1. Stateless backend, horizontal scaling:** Every FastAPI endpoint is stateless — all state lives in ChromaDB, per-user JSON files, or the LTR store. Multiple backend instances can run behind a load balancer without session stickiness. Replacing per-user JSON with Redis gives atomic writes under concurrency.

**2. Vector retrieval scales with job volume:** ChromaDB handles millions of vectors with sub-second retrieval. Batch upserts (32 docs/batch) prevent memory spikes during large job refresh cycles. The freshness boost is applied at query time, not stored, so index structure doesn't change.

**3. LLM provider waterfall absorbs load spikes:** If Ollama is saturated (e.g. during concurrent interview sessions), requests automatically fall through to Groq → Anthropic → Gemini. Adding GPU acceleration to Ollama (via `CUDA` or `Metal`) multiplies local inference throughput.

**4. LTR model is lightweight:** The BPR SGD model is a 12-feature linear model in pure Python — training on 200 preference pairs takes under 100ms. Population and per-user weights are blended (60/40), so new users get reasonable rankings immediately.

**5. Bottlenecks identified:** The agent debate system makes 6–10 LLM calls per `full_analysis` run — this is the primary latency bottleneck. Mitigation: stream debate responses, cache synthesis results per resume hash, or run proposers in parallel threads. SerpAPI is rate-limited; caching job results by MD5 hash with a 5-minute TTL reduces redundant calls significantly.

**6. Docker-ready:** The backend, ChromaDB, and Ollama can each run in a separate container. A `docker-compose.yml` with named volumes for ChromaDB persistence and `ollama pull` in the Ollama container startup brings the full stack up in one command.

---

## Feasibility

**Built and running today:** Every feature listed was built and tested during the hackathon. The system runs end-to-end on a standard laptop with Ollama providing local LLM and embedding inference — no mandatory cloud dependency.

**Minimal infrastructure requirements:** The only hard external dependency is SerpAPI for live job listings (free tier: 100 searches/month). All AI inference runs locally via Ollama. ChromaDB persists to disk with no server required. If Ollama is unavailable, any one of Groq, Anthropic, or Gemini API keys is sufficient to keep the system running.

**Production path is clear:** To take this to production, the changes needed are: (1) swap per-user JSON files for a Redis store with atomic writes, (2) add user authentication (JWT or session-based), (3) containerise with Docker Compose, (4) deploy FastAPI on Render or Railway and the React frontend on Vercel. The CORS configuration, environment variable system, and API surface are already structured for this.

**Dependencies are stable and widely used:** FastAPI, ChromaDB, pdfplumber, python-docx, and Sentence Transformers are all production-grade libraries with active maintenance. There are no experimental or proprietary dependencies that would block deployment.

---

## Novelty

Most career tools are point solutions: LinkedIn shows jobs, Grammarly edits text, LeetCode drills DSA. The few that combine features (like Jobscan or Resume Worded) do so with static keyword matching — they don't use your actual resume to semantically retrieve jobs, adapt to your feedback, or connect resume analysis to interview preparation to learning roadmaps.

Career Genie is different in three specific ways:

**1. Adaptive personalisation loop:** The combination of a feedback signal engine (EMA weight updates) and a pairwise BPR ranking model means the job matching improves with every interaction. This is not a feature claimed by any comparable free or open-source career tool.

**2. Multi-agent debate for career advice:** Rather than a single LLM generating a career plan, three independent proposers generate plans that a critic attacks before a synthesiser produces a final output. This reduces hallucination and surfaces trade-offs the user would otherwise never see. The approach is borrowed from AI safety alignment research and applied here to career decision-making.

**3. Confidence-gated output validation:** Every output from every module passes through a typed validator before being shown. The system knows when it doesn't know — low-confidence outputs are flagged or retried, not silently served. This is a specific gap in existing AI career tools which present all outputs with equal confidence regardless of quality.

**4. Fully local by default:** The entire system can run with zero cloud API calls using Ollama. This matters for users and institutions in regions with data privacy concerns or unreliable internet — a specific gap for the Tamil Nadu institutional use case this project targets.

---

## Feature Depth

**ATS Scorer edge cases handled:**
- LLM response cleaning with 4 fallback parsing strategies (direct JSON → close unclosed braces → fix quote/key issues → regex partial extraction)
- All 10 output fields have typed defaults — a partial LLM response still produces a complete, usable result
- Resume text truncated at 4000 chars, JD at 3000 chars — large enough for real resumes, small enough to stay within context limits

**HR Recruiter Simulation:**
- Returns 10 structured fields: hire verdict (5 options), verdict summary, confidence %, 5 dimension scores (0–10), green flags, red flags, N recruiter questions (each with type and reason), salary bracket, interview rounds, internal notes
- Hire verdict validated against allowed set; dimension scores clamped 0–10; questions normalised to `{question, type, reason}` even if LLM returns plain strings
- Full fallback panel returned on any failure so the UI never goes blank

**Learning-to-Rank model:**
- 12-feature vector per job including affinity scores derived from user history
- Population model (trained on all users) blends with per-user model (60/40) — new users get good rankings immediately, not after 50 interactions
- NDCG@5 evaluated on held-out split after every retrain — model quality is measurable, not assumed

**Job quality filtering:**
- Quality score derived from: base 5.0 + adjustments for red-flag phrases, quality indicator phrases, description length bracket, company name heuristics, apply link presence
- Scam detection via red-flag keyword list built from known patterns

**Confidence system:**
- 4 typed validators: ResumeParseValidator, SkillExtractionValidator, LLMOutputValidator, ConsistencyChecker
- ConsistencyChecker cross-validates ATS score vs advisor output vs job match scores — catches cases where one module produces an outlier

---

## Ethical Use & Disclaimer

Career Genie uses AI-generated content for resume analysis, HR simulation, interview evaluation, and career advice. All outputs are informational only and do not constitute professional career, legal, or financial advice.

**HR Recruiter Simulation:** The hire verdict, dimension scores, and recruiter notes are generated by a language model and are not the opinion of any real recruiter or employer. They should be used as a self-assessment tool, not as a prediction of actual hiring outcomes.

**ATS Scoring:** Scores are approximations based on keyword and format heuristics. They do not reflect the behaviour of any specific company's ATS system.

**Job Matching:** Job listings are retrieved from Google Jobs via SerpAPI. Career Genie does not verify the accuracy, legitimacy, or current availability of any listed position.

**Data:** No user resume data is sent to any external service except the configured LLM provider fallbacks (Groq, Anthropic, Gemini) when Ollama is unavailable. When running fully on Ollama, all data stays local.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built for Origin 2026.

**Team Name:** Neon genesis
**Contact Email:** somaskandan931@gmail.com
