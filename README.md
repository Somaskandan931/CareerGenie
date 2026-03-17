# Career Genie

**Version:** 1.0.0
**Status:** Active Development
**Last Updated:** March 2026

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

Career Genie is a modular AI-powered career intelligence platform. It combines Retrieval-Augmented Generation (RAG), agentic LLM services, and workforce analytics to help job seekers move from resume to offer — with personalized guidance at every step.

The platform addresses a gap in existing job tools: most tools either show job listings or offer generic resume tips, but none connect skill gap analysis, semantic job matching, ATS optimization, mock interviews, and structured learning paths in a single coherent system. Career Genie does all of this, contextualized to the user's actual resume and target role.

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

### Non-Goals

- Career Genie does not guarantee job placement
- The platform does not crawl or aggregate proprietary job board databases; it relies on SerpAPI (Google Jobs)
- Career Genie does not provide legally binding career or financial advice
- Multi-user authentication and per-user data isolation are out of scope for v1.0

---

## 3. System Architecture

Career Genie is organized into five backend engines, each independently responsible for a domain of functionality. All engines are exposed through a FastAPI backend and consumed by a React frontend.

```
Frontend (React + Tailwind CSS)
  Job Matches | Learning | AI Coach | Interview | Insights | Institution Dashboard
                              |
                      FastAPI Backend
                              |
        +-----------+-----------+-------------+------------+
        |           |           |             |            |
   RAG Engine   AI Copilot  Generation    Job Intel    TN Analytics
                  Layer      Engines       Layer         Engine
        |           |           |             |            |
   ChromaDB      Groq LLM   Structured    SerpAPI      NSQF Skill
   (MiniLM)      Inference  JSON Output   + Cache      Taxonomy
```

### Engine Summary

| Engine | Files | Responsibility |
|---|---|---|
| RAG Engine | `matcher.py`, `vector_store.py`, `enhanced_skill_extractor.py` | Semantic job matching and skill comparison |
| AI Copilot Layer | `job_coach.py`, `interview_coach.py`, `career_advisor.py`, `market_insights.py` | Conversational AI, mock interviews, career planning |
| Generation Engines | `roadmap_generator.py`, `project_generator.py` | Structured learning roadmaps and portfolio projects |
| Job Intelligence Layer | `job_scraper.py`, `job_filter.py` | Live job retrieval, quality scoring, scam detection |
| TN Analytics Engine | `tn_automotive_taxonomy.py` | NSQF-based role readiness and batch analytics |

Supporting services: `resume_parser.py`, `resume_rewriter.py`, `ats_scorer.py`, `progress_store.py`

---

## 4. Module Specifications

### 4.1 RAG Engine

#### `vector_store.py` — VectorStore

Manages the ChromaDB vector database used for semantic job retrieval.

- Embeds job documents using `sentence-transformers/all-MiniLM-L6-v2`
- Supports batch upsert (32 docs per batch) with ChromaDB persistence
- Applies a freshness boost during retrieval: jobs posted within 30 days receive a distance penalty reduction of up to 0.1, causing them to rank higher
- Exposes `index_jobs()`, `search()`, `get_stats()`, and `clear()`
- Telemetry is disabled at the environment level to avoid a known `posthog` signature mismatch in newer ChromaDB versions

#### `matcher.py` — JobMatcher

Orchestrates the full matching pipeline: job refresh, RAG retrieval, skill extraction, scoring, and LLM explanation generation.

Match score is computed as a weighted sum:

| Component | Weight | Source |
|---|---|---|
| Semantic similarity (vector distance) | 35% | ChromaDB cosine distance |
| Skill overlap (matched / total job skills) | 45% | Regex skill extraction |
| Title / role alignment | 20% | Keyword and variation matching |
| Critical skill penalty | up to -15 pts | Missing Python, Java, JS, SQL, AWS, React, Docker |

Only matches scoring above 30 are returned. Groq explanations are generated only for matches above 50.

#### `enhanced_skill_extractor.py` — EnhancedSkillExtractor

Extracts skills from free text with surrounding context awareness.

- Skill categories: Python, JavaScript, Machine Learning, Cloud, Databases, DevOps
- Detects proficiency level (beginner / intermediate / proficient / expert) from contextual keywords
- Extracts years of experience using regex patterns
- Deduplicates by category, retaining the highest-proficiency match
- `compare_skills()` produces matched, gap, and bonus skill lists with a numeric overall match percentage

---

### 4.2 AI Copilot Layer

#### `job_coach.py` — JobCoach

A stateless conversational career coach ("Genie") backed by Groq.

- Accepts full conversation history and optional resume context per request
- System prompt instructs the model to give specific, actionable advice across resume review, salary negotiation, role transitions, and job search strategy
- Model: `GROQ_CHAT_MODEL` (configurable)
- Responses are kept to 3–5 sentences unless detail is warranted

#### `interview_coach.py` — InterviewCoach

Conducts mock interviews across three modes: technical, behavioural, and HR.

- `generate_questions()` — Pre-generates a bank of questions with difficulty levels, hints, and ideal answer key points. Returns structured JSON.
- `evaluate_answer()` — Scores a candidate answer 0–10, returns strengths, improvements, a sample better answer, and a follow-up question.
- `chat()` — Runs a live mock interview as a back-and-forth conversation. Automatically opens with a welcome and format explanation on the first turn.

#### `career_advisor.py` — CareerAdvisor

Generates a comprehensive career plan from resume and target role.

- Extracts current skills from resume using a configurable `TECH_SKILLS` list
- Calls Groq to produce a current assessment, 4 skill gaps with importance and level metadata, market insights, and a 5-step action plan
- `_generate_learning_path()` maps skill gaps to curated course resources
- `_generate_career_progression()` returns a three-stage progression (Entry / Mid / Senior) with timelines, key skills, and responsibilities

#### `market_insights.py` — MarketInsights

Combines Google Trends data with Groq-generated analysis.

- Fetches interest-over-time data for up to 10 keywords (role + skills) via `pytrends`
- Splits keywords into chunks of 5 to respect the Google Trends API limit
- Rate-limit handling: exponential back-off with jitter on 429 responses (up to 3 retries per chunk), plus a 3–6 second inter-chunk delay
- In-memory cache with a 6-hour TTL prevents redundant Trends requests within a session
- `_summarise_trend()` computes avg, peak, recent average, direction (rising / stable / falling), and a 12-point sparkline per keyword
- Groq generates a 3-paragraph market analysis with role-specific bullet-point recommendations

---

### 4.3 Generation Engines

#### `roadmap_generator.py` — RoadmapGenerator

Generates a phased, week-by-week learning roadmap structured as JSON.

- Accepts resume text, target role, skill gaps, duration in weeks, and experience level
- Injects verified resource URLs from an internal `RELIABLE_RESOURCES` database into the prompt. Covered topics include: Python, PyTorch, TensorFlow, Docker, Kubernetes, AWS, System Design, BMS, CAN Bus, PLC, and SQL
- Post-processes LLM output to replace null or missing resource URLs with database fallbacks
- Output schema: title, summary, phases (each with weekly tasks, milestones, hours per week), final milestone, and tips

#### `project_generator.py` — ProjectGenerator

Suggests portfolio-building projects tailored to skill gaps and target role.

- Prompts Groq to generate specific, real-world projects — explicitly instructs the model to avoid generic to-do applications
- Output per project: tech stack, skills covered, gap skills addressed, key features, learning outcomes, recruiter impact statement, bonus extensions
- Supports beginner, intermediate, and advanced difficulty levels

---

### 4.4 Job Intelligence Layer

#### `job_scraper.py` — JobScraper

Fetches live job listings from Google Jobs via SerpAPI.

- Parameters: query, location, max jobs (capped at 100), and maximum posting age in days
- Filters out postings older than `days_old` before returning results
- In-memory cache keyed by MD5 hash of (query, location, days_old) with a 5-minute TTL
- Returns structured job dicts with: id, title, company, location, description, apply link, posting date, employment type, and fetch timestamp

#### `job_filter.py` — SmartJobFilter

Post-processes job lists to surface high-quality, relevant postings.

Quality score (0–10) is derived from a base of 5.0 with adjustments:

| Signal | Effect |
|---|---|
| Red-flag keywords (MLM, pyramid, "earn fast") | -2 pts each |
| Quality indicators (benefits, health insurance, career growth) | +0.5 pts each |
| Description length > 500 chars | +1.0 pt |
| Description length < 100 chars | -1.0 pt |
| Legitimate company name (no digits) | +0.5 pts |
| Apply link present | +0.5 pts |

Final sort key: `match_score * 0.7 + quality_score * 30`

---

### 4.5 Resume Services

#### `resume_parser.py` — ResumeParser

Extracts plain text from uploaded resumes.

- PDF: uses `pdfplumber`, page by page
- DOCX: uses `python-docx`, paragraph by paragraph
- Validates that output is non-empty and returns word count alongside extracted text

#### `resume_rewriter.py` — ResumeRewriter

Rewrites resumes for ATS optimization and impact. Three-step pipeline:

1. Full rewrite via Groq with strict rules: professional summary, action verbs, quantified achievements, ATS-friendly section headers, and skill categorization
2. Before/after bullet comparison (4 examples) via a second Groq call
3. Changes summary: word count delta, bullet count delta, action verb count, metrics count, and whether a summary section was added

Falls back to the original resume text if the rewrite call fails.

#### `ats_scorer.py` — ATSScorer

Scores a resume against a target role using Groq. Returns:

- Overall score, keyword score, format score (all 0–100, clamped after parsing)
- Missing keywords, found keywords
- Section-level feedback: experience, skills, education, summary, formatting
- Bullet quality score with specific issues and strong examples
- 6 improvement suggestions
- ATS verdict: Excellent / Good / Needs Work / Poor

A fallback result derived from word count is returned on JSON parse failure or API error.

---

### 4.6 Progress Store

#### `progress_store.py` — ProgressStore

Persistent JSON-backed store for user progress across all modules.

| Section | Key Operations |
|---|---|
| DSA Problems | `get_all_dsa()`, `upsert_dsa_problem()`, `update_dsa_progress()` |
| Roadmap | `get_roadmap_progress()`, `update_roadmap_checkpoint()` |
| Projects | `get_all_projects()`, `upsert_project()`, `update_project()` |
| Interviews | `get_all_interviews()`, `create_interview()`, `add_interview_round()`, `update_interview_outcome()` |
| Summary | `get_summary()` — aggregated dashboard metrics including offer rate and completion percentage |

Storage path defaults to `/tmp/career_genie_progress_store.json` and is configurable via `PROGRESS_STORE_FILE`. All entities use UUID primary keys. Timestamps are stored in UTC ISO 8601 format.

---

### 4.7 TN SkillBridge Engine

#### `tn_automotive_taxonomy.py`

Implements an NSQF-aligned skill taxonomy for Tamil Nadu's automotive sector.

- Maps roles to required skill sets using NSQF qualification levels
- Evaluates individual or batch candidate readiness against role benchmarks
- Intended for institution-facing dashboards used by colleges and training centers

---

## 5. Data Flow

### Job Matching Flow

```
User uploads resume (PDF/DOCX)
        |
   resume_parser.parse() extracts text
        |
   matcher checks vector_store job count
        |--- if < 20 jobs ----> job_scraper.fetch_jobs() --> vector_store.index_jobs()
        |
   vector_store.search(resume_text, top_k * 2)
        |
   enhanced_skill_extractor: extract resume skills + job skills per result
        |
   _calculate_score() [semantic + skill overlap + title match - penalties]
        |--- score < 30: discard
        |--- score > 50: generate Groq explanation
        |
   Return ranked matches with scores, skill gaps, explanations, and apply links
```

### Resume Analysis Flow

```
User uploads resume + specifies target role
        |
   resume_parser.parse() extracts text
        |
        +---------> ats_scorer.score_resume() ---------> Groq --> structured ATS result
        |
        +---------> resume_rewriter.rewrite() ----------> Groq --> rewritten text + comparisons
        |
        +---------> career_advisor.generate_career_advice() --> Groq --> skill gaps + learning path
```

---

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS |
| Backend | FastAPI (Python) |
| LLM Inference | Groq |
| Vector Database | ChromaDB (persistent client) |
| Embeddings | sentence-transformers / all-MiniLM-L6-v2 |
| Trend Data | pytrends (Google Trends API) |
| Job Data | SerpAPI (Google Jobs engine) |
| Resume Parsing | pdfplumber (PDF), python-docx (DOCX) |
| Storage | JSON file (progress store), ChromaDB (vectors) |

---

## 7. Installation and Configuration

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## 8. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for all LLM inference |
| `SERPAPI_KEY` | Yes | SerpAPI key for Google Jobs scraping |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path. Default: `./data/chroma` |
| `PROGRESS_STORE_FILE` | No | Progress JSON path. Default: `/tmp/career_genie_progress_store.json` |
| `GROQ_SMART_MODEL` | No | Groq model ID for structured tasks (scoring, rewriting, roadmaps) |
| `GROQ_CHAT_MODEL` | No | Groq model ID for conversational tasks (coach, interview chat) |
| `EMBEDDING_MODEL` | No | Sentence transformer model name. Default: `all-MiniLM-L6-v2` |
| `MAX_TOKENS_CHAT` | No | Max tokens for chat completions |
| `MAX_TOKENS_CAREER_ADVICE` | No | Max tokens for career advice and ATS scoring |
| `MAX_TOKENS_ROADMAP` | No | Max tokens for roadmap and project generation |
| `MAX_TOKENS_INSIGHTS` | No | Max tokens for market insights analysis |

---

## 9. API Surface

All endpoints accept and return JSON. Organized by engine.

| Group | Endpoint | Method | Description |
|---|---|---|---|
| Resume | `/api/resume/parse` | POST | Upload and parse PDF/DOCX |
| Resume | `/api/resume/score` | POST | ATS score against target role |
| Resume | `/api/resume/rewrite` | POST | ATS-optimized resume rewrite |
| Matching | `/api/jobs/match` | POST | Semantic job match from resume text |
| Matching | `/api/jobs/refresh` | POST | Force-refresh job index from SerpAPI |
| Coaching | `/api/coach/chat` | POST | Job coach conversational turn |
| Interview | `/api/interview/questions` | POST | Generate interview question bank |
| Interview | `/api/interview/evaluate` | POST | Evaluate a candidate answer |
| Interview | `/api/interview/chat` | POST | Live mock interview turn |
| Advisor | `/api/advisor/advice` | POST | Career advice and skill gap analysis |
| Insights | `/api/insights` | POST | Market trends and written analysis |
| Roadmap | `/api/learning/roadmap` | POST | Generate phased learning roadmap |
| Projects | `/api/learning/projects` | POST | Generate portfolio project suggestions |
| Progress | `/api/progress/summary` | GET | Aggregated dashboard summary |
| Progress | `/api/progress/dsa` | GET / POST | DSA problem tracking |
| Progress | `/api/progress/roadmap` | GET / POST | Roadmap checkpoint tracking |
| Progress | `/api/progress/projects` | GET / POST | Project status tracking |
| Progress | `/api/progress/interviews` | GET / POST | Interview pipeline tracking |
| Institution | `/api/institution/analytics` | POST | TN SkillBridge batch analytics |

---

## 10. Known Limitations and Future Work

### Current Limitations

- Progress data is stored per-application in a single JSON file with no per-user isolation. This is intentional for v1.0 but unsuitable for multi-user deployments.
- `pytrends` is subject to Google Trends rate limiting. Under high request volume, trend data may fall back to empty results despite the retry logic.
- Skill extraction in `enhanced_skill_extractor.py` covers six categories. Skills outside these categories (domain-specific tools, emerging frameworks) will not be detected or scored.
- ChromaDB's bundled `posthog` telemetry has a known signature mismatch in some versions. This is suppressed via environment variables; upgrading ChromaDB may require revisiting this workaround.
- SerpAPI results are limited to Google Jobs. Regional job boards and direct company career pages are not covered.

### Planned Enhancements

- Per-user authentication and isolated progress persistence backed by a relational database
- Multi-language support for resumes and coaching responses
- Real-time voice interview simulation
- Expanded skill taxonomy beyond the current six categories
- Cloud deployment with container orchestration (AWS / GCP)
- Integration with professional networking platforms and additional job board APIs
- Advanced personalization using interaction history and user preference modeling