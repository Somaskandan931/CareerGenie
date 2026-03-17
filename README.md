# Career Genie

**Version:** 1.0.0 | **Status:** Active Development | **Last Updated:** March 2026

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
Chroma   Groq    Struct.  SerpAPI  Adaptive  Propose  BPR SGD  Confidence
(MiniLM) LLM     JSON     +Cache   Weights   Critique  Model   Tiers
```

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

- Embeds job documents using `sentence-transformers/all-MiniLM-L6-v2`
- Supports batch upsert (32 docs per batch) with ChromaDB persistence
- Applies a freshness boost during retrieval: jobs posted within 30 days receive a distance penalty reduction of up to 0.1, causing them to rank higher
- Exposes `index_jobs()`, `search()`, `get_stats()`, and `clear()`
- Telemetry is disabled at the environment level to avoid a known `posthog` signature mismatch in newer ChromaDB versions

#### `matcher.py` — JobMatcher

Orchestrates the full matching pipeline: job refresh, RAG retrieval, skill extraction, adaptive scoring, LTR re-ranking, and LLM explanation generation.

Match score is computed as a weighted sum. Weights start at the population prior below and adapt per user over time via the Feedback Engine:

| Component | Default Weight | Source |
|---|---|---|
| Semantic similarity (vector distance) | 35% (adaptive) | ChromaDB cosine distance |
| Skill overlap (matched / total job skills) | 45% (adaptive) | Regex skill extraction |
| Title / role alignment | 20% (adaptive) | Keyword and variation matching |
| Critical skill penalty | up to -15 pts | Missing Python, Java, JS, SQL, AWS, React, Docker |

Per-component scores (`semantic_score`, `skills_score`, `title_score`) are stored on every match result to enable reward attribution during feedback recording and as input features to the LTR model. For users with a feedback history, `personalise_score()` applies an additional ±10 point profile bonus based on role affinity, company affinity, and location preference. After initial matching, the LTR engine re-ranks results using the learned pairwise model when a `user_id` is present.

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

Generates a comprehensive career plan from resume, target role, and cross-agent context.

- Extracts current skills from resume using a configurable `TECH_SKILLS` list
- Accepts ATS score, market insights, and user behaviour profile from other agents, injecting all context into the advice prompt to ground recommendations in real data rather than generic heuristics
- Calls Groq to produce a current assessment, 4 skill gaps with importance and level metadata, market insights, and a 5-step action plan
- `_generate_learning_path()` maps skill gaps to curated course resources
- `_generate_career_progression()` returns a three-stage progression (Entry / Mid / Senior) with timelines, key skills, and responsibilities
- A `context_used` dict is returned with every response, indicating which data sources (ATS, market, profile) were available

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
- A `priority_boost` field is populated per weekly task based on the user's skill interest profile from the Feedback Engine, surfacing high-interest topics earlier

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

### 4.5 Feedback & Learning Engine

#### `feedback_engine.py` — FeedbackEngine

Records user feedback signals, updates adaptive scoring weights, and exposes a personalised scoring API for the matcher. The EMA weights also serve as warm-start inputs to the Learning-to-Rank engine.

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

Weights are updated using an EMA (Exponential Moving Average) gradient step each time a signal is recorded:

```
new_weight[k] += alpha * reward * contribution[k]
weights are re-normalised after each update so they sum to 1
EMA_ALPHA = 0.15  (higher = faster adaptation)
```

Cold-start handling: users with fewer than 5 signals receive blended weights that mix toward the population prior proportionally. This prevents erratic behaviour on the first few interactions.

**User Profile**

Each user accumulates a preference profile derived from their signal history:

- `preferred_roles` — role affinity scores updated on every job interaction
- `preferred_companies` — company affinity scores
- `skill_interest` — interest scores per skill, updated on DSA solves, roadmap completions, and job clicks
- `location_preference` — location affinity from job interactions
- `seniority_signal` — inferred as junior / mid / senior from job titles interacted with

**`personalise_score()`**

Called by the matcher for every job when a `user_id` is present. Combines the adaptive weighted sum of component scores with a profile bonus of up to ±10 points across role, company, and location affinity.

---

### 4.6 Agent Orchestration Layer

#### `agent_orchestrator.py` — AgentOrchestrator

Coordinates five typed agents through a shared `AgentMemory` bus. Integrates the Uncertainty Handler, Learning-to-Rank engine, and Agent Debate System into a single execution loop that implements the full Plan → Act → Reflect → Replan cycle.

**Registered Agents**

| Agent | Responsibilities |
|---|---|
| `ResumeAgent` | ATS scoring, resume rewriting, skill extraction, skill gap analysis |
| `JobAgent` | Job matching, filtering, EMA personalised re-ranking, LTR re-ranking, market insights |
| `InterviewAgent` | Question generation, answer evaluation, session summary with coaching report |
| `RoadmapAgent` | Roadmap generation, project suggestion, feedback-driven topic prioritisation |
| `AdvisorAgent` | Career advice, debate-based synthesis — reads all agent outputs from shared memory, runs the debate loop, and produces a consensus-scored weekly action brief |

**Goal Plans**

Pre-defined multi-step plans available via `run_goal()`:

- `full_analysis` — ATS score → skills → gaps → job match → LTR rank → market insights → roadmap → advice → debate synthesis → consistency check
- `quick_match` — skills → job match → LTR rank
- `interview_prep` — skills → gaps → question generation
- `roadmap_only` — skills → gaps → roadmap → projects → feedback-refined priorities

**Execution Loop**

Every agent output passes through the Uncertainty Handler before being stored in memory. If the confidence score falls below the retry threshold (0.5), the orchestrator automatically retries the step once with the identified issues passed as additional context. After job matching, the LTR engine re-ranks results automatically. For `full_analysis`, the final synthesis step runs the full debate loop instead of a single LLM call. A cross-agent consistency check runs at the end of every goal execution.

**`plan_from_intent()`**

Accepts a free-text user request, uses the LLM planner to decompose it into an ordered task list (max 6 steps), then executes each task with results flowing through shared memory. This is the ReAct-style planning loop.

---

### 4.7 Agent Debate System

#### `agent_debate.py` — DebateOrchestrator

Runs a structured multi-agent debate to produce career recommendations that are stress-tested before being shown to the user. Implements the Propose → Critique → Synthesise → Reflect loop.

**Debate Participants**

| Role | Agent | Perspective |
|---|---|---|
| Proposer | `OptimistProposer` | Opportunity-focused; maximises candidate strengths |
| Proposer | `RealistProposer` | Gap-analysis driven; addresses critical weaknesses first |
| Proposer | `MarketProposer` | Market-demand driven; targets roles with best supply/demand dynamics |
| Critic | `CriticAgent` | Attacks every proposal; assigns confidence scores; flags failure modes |
| Synthesiser | `SynthesisAgent` | Reads all proposals and critiques; merges best elements into a final recommendation |

**Debate Loop**

```
Round 1: All three proposers generate independent plans
         |
         CriticAgent attacks each plan → weaknesses, strengths, confidence, fix
         |
         Convergence check: if avg critic confidence ≥ 0.75, stop early
         |
Round 2: Proposers revise plans using critique as context (if not converged)
         |
         CriticAgent re-evaluates revised plans
         |
SynthesisAgent reads all proposals + critiques → final_answer + consensus_score
         |
ReflectionLayer self-assesses synthesis output
         |--- confidence ≥ 0.6: return result
         |--- confidence < 0.6: RetryController replans with critique hint (up to 2 retries)
```

**`DebateResult`**

Returned by `run_debate()`. Contains the final unified recommendation, all proposals with per-round confidence scores, all critiques, the consensus score (0–1), and a full execution trace.

**`ReflectionLayer`**

After any agent produces output, `ReflectionLayer.reflect()` prompts the model to self-assess its output quality, identify missing elements, and flag whether a retry is warranted. This is the self-reflection step absent in the previous architecture.

**`RetryController`**

Monitors agent outputs against a configurable confidence threshold (default 0.6). When `should_retry=True`, it calls the retry function with the critique hint as context, up to `max_retries` times. This implements the Replan step of the ReAct loop.

**`quick_critique()`**

Lightweight single-round critique of an externally generated plan. Used to validate advisor output without running the full debate.

---

### 4.8 Learning-to-Rank Engine

#### `learning_to_rank.py` — LearningToRankEngine

Replaces population-wide EMA heuristic tuning with a proper pairwise ranking model that learns from individual user preferences using Bayesian Personalised Ranking (BPR) loss with SGD. No external ML dependencies required.

**Feature Vector (12 features per job)**

| Index | Feature | Description |
|---|---|---|
| 0 | `semantic_score` | Normalised vector similarity (0–1) |
| 1 | `skills_score` | Normalised skill overlap ratio (0–1) |
| 2 | `title_score` | Normalised title alignment (0–1) |
| 3 | `recency` | 1.0 for today, 0.0 for 30+ days old |
| 4 | `description_quality` | Length proxy, saturates at 800 chars |
| 5 | `has_apply_link` | Binary (0 or 1) |
| 6 | `role_affinity` | From user profile `preferred_roles` |
| 7 | `company_affinity` | From user profile `preferred_companies` |
| 8 | `location_affinity` | From user profile `location_preference` |
| 9 | `seniority_match` | Alignment between job title seniority and user signal |
| 10 | `skill_gap_penalty` | Inverted — fewer missing skills = higher score |
| 11 | `overall_match` | Normalised overall match score (0–1) |

**Training**

When a user clicks job A instead of job B, a `(winner, loser)` preference pair is recorded. The ranker retrains automatically when 20 new pairs accumulate. Training uses BPR loss with L2 regularisation. The training set is split 80/20 and NDCG@5 is computed on the held-out split after every run.

**Population Model**

Preference pairs from all users are pooled as anonymised feature vectors into a population model retrained every 100 pairs. Per-user models blend with the population model:

```
blended_weight = 0.4 * user_weight + 0.6 * population_weight
```

Cold-start users (fewer than 10 pairs) receive a linearly increasing blend toward their own model as pairs accumulate.

**`rank()`**

Re-ranks a list of job dicts using the blended model. Adds `ltr_score` (0–1) and `ltr_rank` to each job. Called automatically by the orchestrator after `JobAgent.match()`.

**`get_stats()`**

Returns per-user and population model statistics: pair counts, NDCG@5, training loss curve, and a named feature importance dict showing relative weight magnitudes across the 12 features.

---

### 4.9 Uncertainty Handler

#### `uncertainty_handler.py` — UncertaintyHandler

Validates every system output before it is stored in agent memory or returned to the user. Replaces silent failure with structured confidence tiers and actionable issue descriptions.

**Confidence Tiers**

| Tier | Score Range | Behaviour |
|---|---|---|
| `high` | ≥ 0.75 | Show normally |
| `medium` | 0.50 – 0.74 | Show with informational note |
| `low` | 0.25 – 0.49 | Show with warning |
| `unreliable` | < 0.25 | Show fallback or prompt retry |

**Validators**

`ResumeParseValidator` checks: word count (minimum 80), section detection (minimum 2 standard sections), encoding artefacts, and contact information presence.

`SkillExtractionValidator` checks: minimum skill count (2), maximum reasonable count (30), taxonomy coverage (at least 40% of extracted skills must match known tech terms), and cross-reference against the resume text to catch phantom extractions.

`LLMOutputValidator` checks: required field presence, numeric range validity, minimum list lengths, filler/placeholder text detection, and suspiciously short string fields. Applied to ATS scores, career advice, job matches, and roadmaps.

**`ConsistencyChecker`**

Cross-validates outputs from different agents after a full analysis run: ATS missing keywords vs career advisor skill gaps, ATS overall score vs top job match score, and action plan presence relative to available job matches.

**`ConfidenceReport`**

Every validation call returns a `ConfidenceReport` with `score`, `tier`, `issues`, `warnings`, `passed_checks`, `should_retry`, and `fallback_used`. The orchestrator attaches this as a `_confidence` key to every result dict so the frontend can render appropriate caveats without changing business logic.

---

### 4.10 Resume Services

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

### 4.11 Progress Tracker

#### `progress_tracker.py` — ProgressTracker

Tracks user progress across all modules with per-user JSON persistence. Every significant user action emits a typed signal to the Feedback Engine, closing the loop between progress behaviour and job match personalisation.

| Action | Feedback Signal Emitted |
|---|---|
| Complete roadmap task | `view_details` (topic as skill interest) |
| Complete project | `save_job` (skills_covered boost) |
| Add interview application | `apply_click` (role/company affinity) |
| Interview → Offer | `offer_received` (+3.0, strongest signal) |
| Interview → Rejected | `dismiss` (-0.5) |
| Log DSA problem solved | `view_details` (topic as skill) |

Additional metrics tracked:

- `streak` — consecutive active days (current and longest)
- `skill_velocity` — DSA solves per day averaged over the last 7 days
- `retention_risk` — flag set to `true` when the user has been inactive for 3 or more days

| Section | Key Operations |
|---|---|
| DSA Problems | `log_dsa_problem()`, `bulk_update_dsa()`, `get_state()` |
| Roadmap | `import_roadmap()`, `update_task()` |
| Projects | `add_project()`, `update_project()`, `import_projects()` |
| Interviews | `add_interview()`, `update_interview_stage()`, `delete_interview()`, `get_interview_analytics()` |
| Summary | `get_summary()` — dashboard metrics including streak, velocity, retention_risk, offer rate, completion percentage |

---

### 4.12 Progress Store

#### `progress_store.py` — ProgressStore

Persistent JSON-backed store for user progress across all modules (application-level, not per-user). Storage path defaults to `/tmp/career_genie_progress_store.json` and is configurable via `PROGRESS_STORE_FILE`. All entities use UUID primary keys. Timestamps are stored in UTC ISO 8601 format.

| Section | Key Operations |
|---|---|
| DSA Problems | `get_all_dsa()`, `upsert_dsa_problem()`, `update_dsa_progress()` |
| Roadmap | `get_roadmap_progress()`, `update_roadmap_checkpoint()` |
| Projects | `get_all_projects()`, `upsert_project()`, `update_project()` |
| Interviews | `get_all_interviews()`, `create_interview()`, `add_interview_round()`, `update_interview_outcome()` |
| Summary | `get_summary()` — aggregated dashboard metrics including offer rate and completion percentage |

---

### 4.13 TN SkillBridge Engine

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
   uncertainty_handler.wrap_parse()  [confidence check on extracted text]
        |
   matcher checks vector_store job count
        |--- if < 20 jobs ----> job_scraper.fetch_jobs() --> vector_store.index_jobs()
        |
   feedback_engine.get_weights(user_id)  [adaptive or population prior]
        |
   vector_store.search(resume_text, top_k * 2)
        |
   skill extraction + adaptive weighted scoring + critical skill penalty
        |
   feedback_engine.personalise_score()  [profile bonus ±10 pts]
        |--- score < 30: discard
        |--- score > 50: generate Groq explanation
        |
   ltr_engine.rank(user_id, matches)  [pairwise BPR re-ranking]
        |
   uncertainty_handler.wrap_matches()  [confidence check on results]
        |
   Return ranked matches with ltr_score, per-component scores, skill gaps,
   explanations, apply links, and _confidence report
```

### Resume Analysis Flow

```
User uploads resume + specifies target role
        |
   resume_parser.parse() extracts text
        |
        +---------> ats_scorer.score_resume() ---------> Groq --> ATS result
        |               uncertainty_handler.wrap_ats()  [confidence check]
        |
        +---------> resume_rewriter.rewrite() ----------> Groq --> rewritten text
        |
        +---------> career_advisor.generate_career_advice()
                        [with ats_score + market_insights + user_profile]
                        --> Groq --> grounded skill gaps + learning path + action plan
                        uncertainty_handler.wrap_advice()  [confidence check]
```

### Full Analysis Flow (Agent Orchestrator)

```
AgentOrchestrator.run_goal('full_analysis', user_id=...)
        |
   ResumeAgent.ats_score()         --> uncertainty check --> writes ats_score
   ResumeAgent.extract_skills()    --> uncertainty check --> writes resume_skills
   ResumeAgent.parse_gaps()        --> writes skill_gaps
   JobAgent.match()                --> uncertainty check --> writes job_matches
   [auto] ltr_engine.rank()        --> writes ltr_ranked_matches
   JobAgent.market_insights()      --> writes market_insights
   RoadmapAgent.generate()         --> uncertainty check --> writes roadmap
   AdvisorAgent.advise()           --> uncertainty check --> writes career_advice
   AdvisorAgent.debate_synthesise()
        |
        DebateOrchestrator.run_debate()
             OptimistProposer  --> proposal + confidence
             RealistProposer   --> proposal + confidence
             MarketProposer    --> proposal + confidence
             CriticAgent       --> critiques all three proposals
             [if consensus < 0.75: repeat propose + critique]
             SynthesisAgent    --> final_answer + consensus_score
             ReflectionLayer   --> self-assess synthesis
             [if confidence < 0.6: RetryController replans with critique hint]
        |
   uncertainty_handler.check_consistency()  [cross-agent validation]
        |
   Return: results + confidence map + consistency report + debate trace
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
| Ranking Model | Custom BPR SGD (pure Python, zero external ML dependencies) |
| Storage | Per-user JSON files (feedback, progress, LTR models), ChromaDB (vectors) |

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
| `FEEDBACK_STORE_DIR` | No | Feedback engine per-user JSON store path. Default: `/tmp/career_genie_feedback` |
| `PROGRESS_STORE_DIR` | No | Progress tracker per-user JSON path. Default: `/tmp/career_genie_progress` |
| `LTR_STORE_DIR` | No | LTR model per-user JSON store path. Default: `/tmp/career_genie_ltr` |
| `GROQ_SMART_MODEL` | No | Groq model ID for structured tasks (scoring, rewriting, roadmaps, debate) |
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
| Matching | `/api/jobs/match` | POST | Semantic job match with adaptive scoring and LTR re-ranking when `user_id` provided |
| Matching | `/api/jobs/refresh` | POST | Force-refresh job index from SerpAPI |
| Ranking | `/api/ranking/preference` | POST | Record a pairwise job preference (winner/loser) to train the LTR model |
| Ranking | `/api/ranking/stats` | GET | LTR model stats: pair count, NDCG@5, feature importance |
| Feedback | `/api/feedback/record` | POST | Record a user feedback signal (apply, dismiss, offer, etc.) |
| Feedback | `/api/feedback/stats` | GET | Feedback stats, EMA weight drift, top preferred roles |
| Orchestrator | `/api/agent/run` | POST | Execute a multi-agent goal plan (`full_analysis`, `quick_match`, etc.) |
| Orchestrator | `/api/agent/intent` | POST | LLM-planned task decomposition from free-text user intent |
| Debate | `/api/debate/run` | POST | Run a full propose → critique → synthesise debate on a career topic |
| Debate | `/api/debate/critique` | POST | Quick single-round critique of an existing plan |
| Coaching | `/api/coach/chat` | POST | Job coach conversational turn |
| Interview | `/api/interview/questions` | POST | Generate interview question bank |
| Interview | `/api/interview/evaluate` | POST | Evaluate a candidate answer |
| Interview | `/api/interview/chat` | POST | Live mock interview turn |
| Advisor | `/api/advisor/advice` | POST | Career advice and skill gap analysis |
| Insights | `/api/insights` | POST | Market trends and written analysis |
| Roadmap | `/api/learning/roadmap` | POST | Generate phased learning roadmap |
| Projects | `/api/learning/projects` | POST | Generate portfolio project suggestions |
| Progress | `/api/progress/summary` | GET | Aggregated dashboard summary with streak, velocity, and retention risk |
| Progress | `/api/progress/dsa` | GET / POST | DSA problem tracking |
| Progress | `/api/progress/roadmap` | GET / POST | Roadmap checkpoint tracking |
| Progress | `/api/progress/projects` | GET / POST | Project status tracking |
| Progress | `/api/progress/interviews` | GET / POST | Interview pipeline tracking |
| Institution | `/api/institution/analytics` | POST | TN SkillBridge batch analytics |

---

## 10. Known Limitations and Future Work

### Current Limitations

- Progress data in `progress_store.py` is stored per-application in a single JSON file with no per-user isolation. This is intentional for v1.0 but unsuitable for multi-user deployments.
- `pytrends` is subject to Google Trends rate limiting. Under high request volume, trend data may fall back to empty results despite the retry logic.
- Skill extraction in `enhanced_skill_extractor.py` covers six categories. Skills outside these categories (domain-specific tools, emerging frameworks) will not be detected or scored.
- ChromaDB's bundled `posthog` telemetry has a known signature mismatch in some versions. This is suppressed via environment variables; upgrading ChromaDB may require revisiting this workaround.
- SerpAPI results are limited to Google Jobs. Regional job boards and direct company career pages are not covered.
- Feedback Engine and LTR model state are persisted in per-user JSON files. Under concurrent or multi-server deployments, last-write-wins semantics may cause update collisions. A Redis-backed atomic store is the recommended upgrade path for both.
- Agent Orchestrator uses a single in-process `AgentMemory` instance per session. Memory does not persist across requests without explicit serialisation; each `run_goal()` call starts with a fresh memory bus unless state is pre-loaded by the caller.
- The LTR model requires a minimum of 10 user preference pairs before per-user weights are active. Users with fewer interactions receive population-blended weights.
- The debate system runs up to 2 rounds with 3 proposers and 1 critic, generating 6–9 Groq calls per `full_analysis` run. This increases latency by 8–15 seconds compared to single-pass synthesis. A streaming response mode is the recommended mitigation.
- `learning_to_rank.py` references its own module path (`backend.services.learning_to_rank`) for a population training step. This requires the file to be placed at exactly `backend/services/learning_to_rank.py` with `backend` on `PYTHONPATH`.

### Planned Enhancements

- Per-user authentication and isolated progress persistence backed by a relational database
- Multi-language support for resumes and coaching responses
- Real-time voice interview simulation
- Expanded skill taxonomy beyond the current six categories
- Cloud deployment with container orchestration (AWS / GCP)
- Integration with professional networking platforms and additional job board APIs
- Persistent agent memory across sessions with vector-backed episodic recall
- Nightly batch summarisation of feedback signals (`FeedbackEngine.summarise_day`) via scheduled job (Celery beat / cron)
- Streaming debate responses to reduce perceived latency on `full_analysis` runs
- Neural re-ranker replacing the linear BPR model once sufficient training pairs are available (target: 500+ pairs per user)
- Offline A/B evaluation framework comparing EMA, BPR, and neural ranker strategies on held-out preference logs