
# Career Genie

**Version:** 2.0.0 | **Status:** Active Development | **Last Updated:** April 2026

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [System Architecture](#3-system-architecture)
4. [Module Specifications](#4-module-specifications)
5. [Data Flow](#5-data-flow)
6. [Technology Stack](#6-technology-stack)
7. [Installation and Configuration](#7-installation-and-configuration)
8. [Environment Variables](#8-environment-variables)
9. [API Surface](#9-api-surface)
10. [Known Limitations and Future Work](#10-known-limitations-and-future-work)

---

## 1. Product Overview

Career Genie is a modular AI-powered career intelligence platform. It combines Retrieval-Augmented Generation (RAG), a multi-agent debate and orchestration layer, a pairwise learning-to-rank engine, and workforce analytics to help job seekers move from resume to offer — with personalized guidance at every step.

The platform addresses a gap in existing job tools: most tools either show job listings or offer generic resume tips, but none connect skill gap analysis, semantic job matching, ATS optimization, mock interviews, and structured learning paths in a single coherent system. Career Genie does all of this, contextualized to the user's actual resume and target role, with every recommendation validated for confidence before being surfaced.

### Primary Users

- Job seekers preparing for technical and non-technical roles
- Career changers assessing skill gaps and transition paths
- Institution administrators (colleges, training centers) monitoring batch readiness via the TN SkillBridge dashboard

---

## 2. Goals and Non-Goals

### Goals

- Provide semantically accurate job matching based on resume content, not just keyword overlap
- Generate actionable, personalized career plans including roadmaps, projects, and skill gap analysis
- Simulate realistic interview experiences with scored feedback
- Score and rewrite resumes for ATS compatibility
- Surface real-time market demand data for target roles and skills
- Track user progress across DSA practice, roadmap completion, projects, and interview pipeline
- Record user feedback signals and adapt job match rankings over time using a pairwise learning-to-rank model trained on revealed preferences
- Coordinate multiple AI agents through a shared memory bus, debate loop, and cross-agent consistency validation to produce unified career guidance
- Flag low-confidence outputs and degrade gracefully rather than silently failing
- **NEW:** Run fully locally using Ollama as the primary LLM and embedding provider

### Non-Goals

- Career Genie does not guarantee job placement
- The platform does not crawl or aggregate proprietary job board databases; it relies on SerpAPI (Google Jobs)
- Career Genie does not provide legally binding career or financial advice
- Multi-user authentication and per-user data isolation are out of scope for v1.0

---

## 3. System Architecture

Career Genie is organized into backend engines, each independently responsible for a domain of functionality. All engines are exposed through a FastAPI backend and consumed by a React frontend.

```
Frontend (React + Tailwind CSS)
  Job Matches | Learning | AI Coach | Interview | Insights | Institution Dashboard
                              |
                      FastAPI Backend
                              |
  +--------+--------+--------+--------+--------+--------+--------+--------+
  |        |        |        |        |        |        |        |        |
 RAG    AI Copilot  Gen    Job Intel  Feedback  Agent   Ranking Uncertainty
Engine   Layer    Engines   Layer    & Learning Debate  (LTR)   Handler
  |        |        |        |        |        |        |        |
Chroma   Ollama   Struct.  SerpAPI  Adaptive  Propose  BPR SGD  Confidence
(Ollama  (Primary) JSON     +Cache   Weights   Critique  Model   Tiers
Embed)
```

### Provider Waterfall (NEW)

| Priority | Provider | Type | Requirements |
|----------|----------|------|--------------|
| 1 | Ollama (llama3.2:3b) | Local LLM | `ollama serve` running |
| 2 | Groq (Llama 3.3 70B) | Cloud Fallback | `GROQ_API_KEY` |
| 3 | Anthropic (Claude) | Cloud Fallback | `ANTHROPIC_API_KEY` |
| 4 | Gemini | Cloud Fallback | `GEMINI_API_KEY` |

### Embedding Waterfall (NEW)

| Priority | Provider | Type | Requirements |
|----------|----------|------|--------------|
| 1 | Ollama (all-minilm) | Local Embeddings | `ollama serve` running |
| 2 | Sentence Transformers | Local Fallback | First download from Hugging Face |

### Engine Summary

| Engine | Files | Responsibility |
|---|---|---|
| RAG Engine | `matcher.py`, `vector_store.py`, `enhanced_skill_extractor.py` | Semantic job matching and skill comparison |
| AI Copilot Layer | `job_coach.py`, `interview_coach.py`, `career_advisor.py`, `market_insights.py` | Conversational AI, mock interviews, career planning |
| Generation Engines | `roadmap_generator.py`, `project_generator.py` | Structured learning roadmaps and portfolio projects |
| Job Intelligence Layer | `job_scraper.py`, `job_filter.py` | Live job retrieval, quality scoring, scam detection |
| Feedback & Learning Engine | `feedback_engine.py` | Feedback signal recording, EMA weight updates, user profile building, personalised scoring |
| Agent Orchestration Layer | `agent_orchestrator.py` | Multi-agent task planning, shared memory bus, debate synthesis, uncertainty-gated execution |
| Agent Debate System | `agent_debate.py` | Propose → Critique → Synthesise → Reflect loop with retry controller |
| Learning-to-Rank Engine | `learning_to_rank.py` | Pairwise BPR ranking model, per-user and population models, NDCG evaluation |
| Uncertainty Handler | `uncertainty_handler.py` | Confidence scoring, output validation, cross-agent consistency checking |
| TN Analytics Engine | `tn_automotive_taxonomy.py` | NSQF-based role readiness and batch analytics |

Supporting services: `resume_parser.py`, `resume_rewriter.py`, `ats_scorer.py`, `progress_store.py`, `progress_tracker.py`

---

## 4. Module Specifications

### 4.1 RAG Engine

#### `vector_store.py` — VectorStore

Manages the ChromaDB vector database used for semantic job retrieval.

- Embeds job documents using **Ollama all-minilm** (primary) or Sentence Transformers (fallback)
- Supports batch upsert (32 docs per batch) with ChromaDB persistence
- Applies a freshness boost during retrieval: jobs posted within 30 days receive a distance penalty reduction of up to 0.1, causing them to rank higher
- Exposes `index_jobs()`, `search()`, `get_stats()`, and `clear()`
- Telemetry is disabled at the environment level to avoid a known `posthog` signature mismatch

#### `matcher.py` — JobMatcher

Orchestrates the full matching pipeline: job refresh, RAG retrieval, skill extraction, adaptive scoring, LTR re-ranking, and LLM explanation generation.

Match score is computed as a weighted sum. Weights start at the population prior below and adapt per user over time via the Feedback Engine:

| Component | Default Weight | Source |
|---|---|---|
| Semantic similarity (vector distance) | 35% (adaptive) | ChromaDB cosine distance |
| Skill overlap (matched / total job skills) | 45% (adaptive) | Regex skill extraction |
| Title / role alignment | 20% (adaptive) | Keyword and variation matching |
| Critical skill penalty | up to -15 pts | Missing Python, Java, JS, SQL, AWS, React, Docker |

Per-component scores are stored on every match result to enable reward attribution. For users with a feedback history, `personalise_score()` applies an additional ±10 point profile bonus. After initial matching, the LTR engine re-ranks results using the learned pairwise model when a `user_id` is present.

#### `enhanced_skill_extractor.py` — EnhancedSkillExtractor

Extracts skills from free text with surrounding context awareness.

- Skill categories: Python, JavaScript, Machine Learning, Cloud, Databases, DevOps
- Detects proficiency level (beginner / intermediate / proficient / expert) from contextual keywords
- Extracts years of experience using regex patterns
- Deduplicates by category, retaining the highest-proficiency match

---

### 4.2 AI Copilot Layer

#### `job_coach.py` — JobCoach

A stateless conversational career coach ("Genie") backed by Ollama (primary) with cloud fallbacks.

- Accepts full conversation history and optional resume context per request
- System prompt instructs the model to give specific, actionable advice
- Automatic retry logic with exponential backoff (3 attempts)

#### `interview_coach.py` — InterviewCoach

Conducts mock interviews across three modes: technical, behavioural, and HR.

- `generate_questions()` — Pre-generates a question bank with difficulty levels, hints, and ideal answer key points
- `evaluate_answer()` — Scores a candidate answer 0–10, returns strengths, improvements, a sample better answer, and a follow-up question
- `chat()` — Runs a live mock interview as a back-and-forth conversation

#### `career_advisor.py` — CareerAdvisor

Generates a comprehensive career plan from resume, target role, and cross-agent context.

- Extracts current skills from resume using a configurable `TECH_SKILLS` list
- Accepts ATS score, market insights, and user behaviour profile from other agents
- Calls Ollama (primary) to produce a current assessment, 4 skill gaps with importance and level metadata, market insights, and a 5-step action plan

#### `market_insights.py` — MarketInsights

Combines Google Trends data with LLM-generated analysis.

- Fetches interest-over-time data for up to 10 keywords via `pytrends`
- Rate-limit handling: exponential back-off with jitter on 429 responses (up to 3 retries per chunk)
- In-memory cache with a 6-hour TTL
- Generates analysis using Ollama (primary) with fallback to Groq and a template-based fallback when LLM unavailable

---

### 4.3 Generation Engines

#### `roadmap_generator.py` — RoadmapGenerator

Generates a phased, week-by-week learning roadmap structured as JSON.

- Accepts resume text, target role, skill gaps, duration in weeks, and experience level
- Injects verified resource URLs from an internal `RELIABLE_RESOURCES` database
- Post-processes LLM output to replace null or missing resource URLs with database fallbacks

#### `project_generator.py` — ProjectGenerator

Suggests portfolio-building projects tailored to skill gaps and target role.

- Prompts Ollama to generate specific, real-world projects
- Output per project: tech stack, skills covered, gap skills addressed, key features, learning outcomes, recruiter impact statement, bonus extensions

---

### 4.4 Job Intelligence Layer

#### `job_scraper.py` — JobScraper

Fetches live job listings from Google Jobs via SerpAPI.

- Parameters: query, location, max jobs (capped at 100), and maximum posting age in days
- In-memory cache keyed by MD5 hash with a 5-minute TTL
- Returns structured job dicts with: id, title, company, location, description, apply link, posting date

#### `job_filter.py` — SmartJobFilter

Post-processes job lists to surface high-quality, relevant postings.

Quality score (0–10) is derived from a base of 5.0 with adjustments for red-flag keywords, quality indicators, description length, company name legitimacy, and apply link presence.

---

### 4.5 Feedback & Learning Engine

#### `feedback_engine.py` — FeedbackEngine

Records user feedback signals, updates adaptive scoring weights, and exposes a personalised scoring API.

**Signal Types and Rewards**

| Signal | Reward |
|---|---|
| `offer_received` | +3.0 |
| `interview_landed` | +2.0 |
| `apply_click` | +1.0 |
| `rate_match_up` | +0.8 |
| `save_job` | +0.6 |
| `view_details` | +0.3 |
| `scroll_past` | -0.1 |
| `dismiss` | -0.5 |
| `rate_match_down` | -0.8 |

**Adaptive Weight Update**

Weights are updated using EMA (Exponential Moving Average) with `EMA_ALPHA = 0.15`. Cold-start users (fewer than 5 signals) receive blended weights toward the population prior.

---

### 4.6 Agent Orchestration Layer

#### `agent_orchestrator.py` — AgentOrchestrator

Coordinates five typed agents through a shared `AgentMemory` bus.

**Registered Agents**

| Agent | Responsibilities |
|---|---|
| `ResumeAgent` | ATS scoring, resume rewriting, skill extraction |
| `JobAgent` | Job matching, filtering, LTR re-ranking, market insights |
| `InterviewAgent` | Question generation, answer evaluation, session summary |
| `RoadmapAgent` | Roadmap generation, project suggestion, feedback-driven prioritisation |
| `AdvisorAgent` | Career advice, debate-based synthesis |

**Goal Plans**

- `full_analysis` — Complete analysis including debate synthesis
- `quick_match` — Skills → job match → LTR rank
- `interview_prep` — Skills → gaps → question generation
- `roadmap_only` — Skills → gaps → roadmap → projects

---

### 4.7 Agent Debate System

#### `agent_debate.py` — DebateOrchestrator

Runs a structured multi-agent debate to produce career recommendations that are stress-tested before being shown to the user.

**Debate Participants**

| Role | Agent | Perspective |
|---|---|---|
| Proposer | `OptimistProposer` | Opportunity-focused |
| Proposer | `RealistProposer` | Gap-analysis driven |
| Proposer | `MarketProposer` | Market-demand driven |
| Critic | `CriticAgent` | Attacks every proposal |
| Synthesiser | `SynthesisAgent` | Merges best elements |

**Debate Loop**

- Round 1: Three proposers generate independent plans
- Critic attacks each plan → weaknesses, strengths, confidence
- Convergence check: if avg critic confidence ≥ 0.75, stop early
- Round 2: Proposers revise using critique (if not converged)
- SynthesisAgent produces final answer + consensus score
- ReflectionLayer self-assesses output; RetryController replans if confidence < 0.6

---

### 4.8 Learning-to-Rank Engine

#### `learning_to_rank.py` — LearningToRankEngine

Replaces population-wide EMA heuristic tuning with a proper pairwise ranking model using Bayesian Personalised Ranking (BPR) loss with SGD.

**Feature Vector (12 features per job)**

| Index | Feature | Description |
|---|---|---|
| 0 | `semantic_score` | Normalised vector similarity |
| 1 | `skills_score` | Normalised skill overlap ratio |
| 2 | `title_score` | Normalised title alignment |
| 3 | `recency` | 1.0 for today, 0.0 for 30+ days old |
| 4 | `description_quality` | Length proxy |
| 5 | `has_apply_link` | Binary |
| 6-8 | Affinity scores | Role, company, location from user profile |
| 9 | `seniority_match` | Job title vs user seniority signal |
| 10 | `skill_gap_penalty` | Inverted missing skill count |
| 11 | `overall_match` | Normalised overall match score |

**Training**

- Auto-retrains when 20 new preference pairs accumulate
- BPR loss with L2 regularisation
- NDCG@5 computed on held-out split after every run
- Population model blends with per-user models: `0.4 * user + 0.6 * population`

---

### 4.9 Uncertainty Handler

#### `uncertainty_handler.py` — UncertaintyHandler

Validates every system output before it is stored in agent memory or returned to the user.

**Confidence Tiers**

| Tier | Score Range | Behaviour |
|---|---|---|
| `high` | ≥ 0.75 | Show normally |
| `medium` | 0.50 – 0.74 | Show with note |
| `low` | 0.25 – 0.49 | Show with warning |
| `unreliable` | < 0.25 | Show fallback or retry |

**Validators**

- `ResumeParseValidator` — word count, section detection, encoding artefacts
- `SkillExtractionValidator` — minimum count, taxonomy coverage, cross-reference
- `LLMOutputValidator` — required fields, numeric ranges, filler text detection
- `ConsistencyChecker` — cross-validates ATS vs advisor vs job matches

---

### 4.10 Resume Services

#### `resume_parser.py` — ResumeParser

Extracts plain text from uploaded resumes (PDF via pdfplumber, DOCX via python-docx).

#### `resume_rewriter.py` — ResumeRewriter

Rewrites resumes for ATS optimization with professional summary, action verbs, quantified achievements, and ATS-friendly formatting.

#### `ats_scorer.py` — ATSScorer

Scores a resume against a target role, returning overall score, keyword score, format score, missing/found keywords, section feedback, bullet quality analysis, and improvement suggestions.

---

### 4.11 Progress Tracker

#### `progress_tracker.py` — ProgressTracker

Tracks user progress across all modules with per-user JSON persistence. Every significant user action emits a typed signal to the Feedback Engine.

**Tracked Sections**

| Section | Key Operations |
|---|---|
| DSA Problems | `log_dsa_problem()`, `bulk_update_dsa()` |
| Roadmap | `import_roadmap()`, `update_task()` |
| Projects | `add_project()`, `update_project()` |
| Interviews | `add_interview()`, `update_interview_stage()` |

**Additional Metrics**

- `streak` — consecutive active days
- `skill_velocity` — DSA solves per day (last 7 days)
- `retention_risk` — inactive for 3+ days

---

### 4.12 TN SkillBridge Engine

#### `tn_automotive_taxonomy.py`

Implements an NSQF-aligned skill taxonomy for Tamil Nadu's automotive sector with 20 skills, 7 job roles, NSQF levels 1-7, and training source recommendations.

---

## 5. Data Flow

### Job Matching Flow (Updated with Ollama)

```
User uploads resume (PDF/DOCX)
        |
   resume_parser.parse() extracts text
        |
   uncertainty_handler.wrap_parse() [confidence check]
        |
   matcher checks vector_store job count
        |--- if < 20 jobs ----> job_scraper.fetch_jobs() --> vector_store.index_jobs()
        |                         (Ollama embeddings for indexing)
        |
   feedback_engine.get_weights(user_id)
        |
   vector_store.search(resume_text, top_k * 2)
        | (Ollama embeddings for query)
        |
   skill extraction + adaptive weighted scoring + critical skill penalty
        |
   feedback_engine.personalise_score() [profile bonus ±10 pts]
        |
   ltr_engine.rank(user_id, matches) [pairwise BPR re-ranking]
        |
   uncertainty_handler.wrap_matches() [confidence check]
        |
   Return ranked matches with ltr_score, skill gaps, explanations
```

### LLM Provider Waterfall

```
LLM Request
        |
   Try Ollama (local)
        |--- Success: Return response
        |--- Failure: Log warning, continue
        |
   Try Groq (cloud fallback)
        |--- Success: Return response
        |--- Failure: Continue
        |
   Try Anthropic (cloud fallback)
        |--- Success: Return response
        |--- Failure: Continue
        |
   Try Gemini (cloud fallback)
        |--- Success: Return response
        |--- Failure: Raise error
```

---

## 6. Technology Stack (Updated)

| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS |
| Backend | FastAPI (Python 3.10+) |
| Primary LLM | **Ollama (llama3.2:3b)** - Local inference |
| LLM Fallback 1 | Groq (Llama 3.3 70B) |
| LLM Fallback 2 | Anthropic Claude |
| LLM Fallback 3 | Gemini |
| Primary Embeddings | **Ollama (all-minilm)** - 384-dim vectors |
| Embeddings Fallback | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector Database | ChromaDB (persistent client) |
| Trend Data | pytrends (Google Trends API) |
| Job Data | SerpAPI (Google Jobs engine) |
| Resume Parsing | pdfplumber (PDF), python-docx (DOCX) |
| Ranking Model | Custom BPR SGD (pure Python) |
| Storage | Per-user JSON files, ChromaDB (vectors) |

---

## 7. Installation and Configuration (Updated)

### Prerequisites

1. **Install Ollama** (Primary LLM Provider)
   - Download from https://ollama.com/download
   - Run `ollama serve` in a terminal
   - Pull models: `ollama pull all-minilm` and `ollama pull llama3.2:3b`

2. **Install Python 3.10+** and create virtual environment

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Start Ollama (in a separate terminal)
ollama serve

# Start backend
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Quick Test

```bash
# Test Ollama is working
python test_ollama_setup.py

# Test backend health
curl http://localhost:8000/health
```

---

## 8. Environment Variables (Updated)

| Variable | Required | Description |
|---|---|---|
| `OLLAMA_HOST` | No | Ollama API host. Default: `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | No | Ollama embedding model. Default: `all-minilm` |
| `OLLAMA_LLM_MODEL` | No | Ollama LLM model. Default: `llama3.2:3b` |
| `GROQ_API_KEY` | No* | Groq API key (fallback when Ollama unavailable) |
| `ANTHROPIC_API_KEY` | No* | Anthropic API key (secondary fallback) |
| `GEMINI_API_KEY` | No* | Gemini API key (tertiary fallback) |
| `SERPAPI_KEY` | Yes | SerpAPI key for Google Jobs scraping |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path. Default: `./data/chroma` |
| `FEEDBACK_STORE_DIR` | No | Feedback engine store path. Default: `/tmp/career_genie_feedback` |
| `LTR_STORE_DIR` | No | LTR model store path. Default: `/tmp/career_genie_ltr` |

*\* At least one LLM provider must be available (Ollama recommended, or any cloud API key)*

---

## 9. API Surface

All endpoints accept and return JSON.

| Group | Endpoint | Method | Description |
|---|---|---|---|
| Resume | `/upload-resume/parse` | POST | Upload and parse PDF/DOCX |
| Resume | `/ats/score` | POST | ATS score against target role |
| Resume | `/resume/rewrite` | POST | ATS-optimized resume rewrite |
| Matching | `/rag/match-realtime` | POST | Semantic job match with LTR re-ranking |
| Ranking | `/ranking/preference` | POST | Record pairwise job preference |
| Ranking | `/ranking/stats` | GET | LTR model stats |
| Feedback | `/feedback/record` | POST | Record user feedback signal |
| Feedback | `/feedback/stats` | GET | Feedback stats and weight drift |
| Orchestrator | `/agent/run` | POST | Execute multi-agent goal plan |
| Orchestrator | `/agent/intent` | POST | LLM-planned task decomposition |
| Debate | `/debate/run` | POST | Run full propose-critique-synthesise debate |
| Coaching | `/coach/chat` | POST | Job coach conversational turn |
| Interview | `/interview/questions` | POST | Generate interview question bank |
| Interview | `/interview/evaluate` | POST | Evaluate candidate answer |
| Interview | `/interview/chat` | POST | Live mock interview turn |
| Insights | `/insights/market` | POST | Market trends and analysis |
| Roadmap | `/generate/roadmap` | POST | Generate phased learning roadmap |
| Projects | `/generate/projects` | POST | Generate portfolio project suggestions |
| Progress | `/progress/{user_id}/summary` | GET | Dashboard summary with streak/velocity |
| TN | `/tn/batch-analytics` | POST | TN SkillBridge batch analytics |

---

## 10. Known Limitations and Future Work

### Current Limitations

- Ollama requires separate installation and `ollama serve` to be running before backend starts
- First-time embedding generation with Ollama may have higher latency due to model loading
- `pytrends` is subject to Google Trends rate limiting
- Skill extraction covers limited categories; emerging frameworks may not be detected
- ChromaDB telemetry has known signature mismatch (suppressed via environment variables)
- SerpAPI results limited to Google Jobs only
- Per-user JSON storage has last-write-wins semantics under concurrency
- LTR model requires minimum 10 user preference pairs before per-user weights activate
- Debate system generates multiple LLM calls per `full_analysis` run, increasing latency

### Planned Enhancements

- Docker Compose setup with Ollama, ChromaDB, and backend in one command
- GPU acceleration for Ollama inference
- Per-user authentication and isolated progress persistence
- Multi-language support for resumes and coaching
- Real-time voice interview simulation
- Expanded skill taxonomy beyond current categories
- Redis-backed atomic store for Feedback Engine and LTR models
- Streaming debate responses to reduce perceived latency
- Neural re-ranker replacing linear BPR model
- Offline A/B evaluation framework for ranking strategies
