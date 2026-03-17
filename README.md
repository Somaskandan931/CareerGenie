<div align="center">

# Career Genie · TN AUTO SkillBridge

**AI-Powered Job Discovery · Skill Gap Analysis · Personalized Learning Paths · TN Automotive & EV Workforce Analytics**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Claude AI](https://img.shields.io/badge/Claude_AI-Sonnet_4-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![NSQF](https://img.shields.io/badge/NSQF-Aligned-orange?style=for-the-badge)](https://nqr.gov.in)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-features) · [Architecture](#-architecture) · [Getting Started](#-getting-started) · [Usage](#-usage) · [API Reference](#-api-reference) · [TN Automotive Module](#-tn-automotive-module) · [Contributing](#-contributing)

</div>

---

## What is Career Genie?

Career Genie is an intelligent career platform that uses **RAG (Retrieval Augmented Generation)** to match your resume with live job listings, identify skill gaps, generate week-by-week learning roadmaps, and suggest hands-on projects — all powered by Claude AI.

It also includes **TN AUTO SkillBridge** — a dedicated institutional analytics layer for Tamil Nadu's automotive and EV ecosystem, aligned with **Naan Mudhalvan**, **TNSDC**, and **NSQF levels 1–7**.

> Upload your resume → search for roles → get a personalized plan to land the job.
> Or, if you're a training officer → upload a student batch → get cohort-level skill gap reports instantly.

---

## Features

### 🔍 Smart Job Matching
- **RAG-Powered Matching** — Vector embeddings and semantic search surface jobs that fit *your* experience, not just keyword matches
- **Real-time Job Search** — Pulls live listings from Google Jobs via SerpAPI
- **AI Match Explanations** — Claude tells you exactly *why* each job is a fit
- **Match Scoring** — Detailed 0–100% scores with per-skill breakdowns

### 📊 Skill Assessment Dashboard
- Visual skill categorisation and proficiency scoring
- **Matched Skills** — What you already bring to the table
- **Skill Gaps** — Critical skills to develop, ranked by importance
- **Bonus Skills** — Your differentiators beyond the job description

### 💡 Career Guidance
- AI-generated assessment of your current standing
- Curated learning paths with specific courses and resources
- Career progression roadmap: Entry → Mid → Senior
- Salary expectations, market insights, and actionable next steps

### 🗺️ Career Roadmaps & Projects
- **Personalised Roadmaps** — Week-by-week learning plans built from your actual skill gaps
- **Milestone Tracking** — Visual progress checkpoints you can mark complete
- **Hands-on Project Suggestions** — Curated projects with difficulty, time estimates, and tech stacks
- **Portfolio Builder** — Track completed projects across difficulty levels

### 🏭 TN AUTO SkillBridge *(New)*
- **TN Automotive Skill Taxonomy** — 21 domain-specific skills covering EV, CNC, PLC, welding, IATF quality, and more
- **NSQF Level Mapping** — Every skill mapped to NSQF levels 1–7 with institutional equivalents
- **Single Profile Analysis** — Analyze one student against a specific TN job role
- **Batch Cohort Analytics** — Upload up to 500 ITI/polytechnic student profiles, get a full heatmap report
- **Training Recommendations** — Per-gap suggestions from Naan Mudhalvan modules, TNSDC, SIEMENS Skill Centre, and more
- **Role Readiness Scoring** — Shows what % of a batch is job-ready vs. needs upskilling
- **Downloadable Reports** — Export full cohort analytics as JSON for skill council submissions

### 🔧 Advanced Filtering
- Experience level: Entry / Mid / Senior
- Minimum match score threshold
- Job recency: 7 / 14 / 30 / 60 days
- Remote / on-site preference
- Quality scoring to filter out scam listings

---

## Architecture

```
┌──────────────────────────────────────┐
│           React Frontend             │
│   Job Matches · Learning · Institution│
│          (Tailwind CSS)              │
└──────────────┬───────────────────────┘
               │ REST API
               ▼
┌──────────────────────────────────────┐
│          FastAPI Backend             │
├──────────────────────────────────────┤
│  Resume Parser                       │
│  Job Scraper          (SerpAPI)      │
│  Vector Store         (ChromaDB)     │
│  AI Matcher           (Claude)       │
│  Career Advisor       (Claude)       │
│  Roadmap Generator    (Claude) ← New │
│  Project Generator    (Claude) ← New │
│  TN Automotive Taxonomy       ← New  │
│  Batch Analytics Engine       ← New  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│         External Services            │
├──────────────────────────────────────┤
│  SerpAPI            (live jobs)      │
│  Claude Sonnet 4    (AI)             │
│  ChromaDB           (vectors)        │
│  Sentence Transformers (embeddings)  │
└──────────────────────────────────────┘
```

### RAG Pipeline

```
Resume + Job Description
        │
        ▼
1. RETRIEVE  →  Semantic search over ChromaDB vector store
2. AUGMENT   →  Combine resume context + job desc + matched skills
3. GENERATE  →  Claude produces explanations, roadmaps, projects
```

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.8+ |
| Node.js | 16+ |
| npm / yarn | Latest |

### API Keys

| Service | Purpose | Where to Get |
|---------|---------|--------------|
| **Anthropic** | AI matching, roadmaps, advice | [console.anthropic.com](https://console.anthropic.com/) |
| **SerpAPI** | Live job search (100 free/month) | [serpapi.com](https://serpapi.com/) |

---

## Installation

### 1. Clone

```bash
git clone https://github.com/somaskandan931/career-genie.git
cd career-genie
```

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOL
SERPAPI_KEY=your_serpapi_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_db
MAX_TOKENS_CAREER_ADVICE=2000
MAX_TOKENS_ROADMAP=3000
EOL

# Start server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend/resume-frontend
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000)

---

## Usage

### Individual User Flow

| Step | Action |
|------|--------|
| **1. Upload Resume** | Upload PDF or DOCX — system extracts skills automatically |
| **2. Search Jobs** | Enter title + location, apply filters (level, recency, remote) |
| **3. Review Matches** | See match scores, explanations, matched skills, and gaps |
| **4. Get Career Guidance** | Explore learning resources, roadmap, and market insights |
| **5. Generate Roadmap** | Switch to Learning Path tab, enter target role, generate plan |
| **6. Track Progress** | Mark milestones complete, save projects to your portfolio |

### Institutional User Flow (Training Officers / Skill Councils)

| Step | Action |
|------|--------|
| **1. Open Institution Tab** | Click "Institution" in the top navigation |
| **2. Enter Batch Name** | Enter your ITI / polytechnic and batch name |
| **3. Upload Profiles** | Paste student profiles as JSON or click "Run Demo" |
| **4. View Analytics** | See NSQF distribution, role readiness, and skill gap heatmap |
| **5. Plan Training** | Use the auto-generated action plan to schedule courses |
| **6. Download Report** | Export the full cohort report for skill council submissions |

---

## Project Structure

```
career-genie/
├── backend/
│   ├── services/
│   │   ├── career_advisor.py           # AI career guidance
│   │   ├── enhanced_skill_extractor.py # Proficiency-aware skill extraction
│   │   ├── job_filter.py               # Quality scoring & scam filtering
│   │   ├── job_scraper.py              # SerpAPI integration
│   │   ├── matcher.py                  # RAG-based job matching
│   │   ├── resume_parser.py            # PDF/DOCX parsing
│   │   ├── vector_store.py             # ChromaDB integration
│   │   ├── roadmap_generator.py        # AI roadmap generation  ← New
│   │   ├── project_generator.py        # AI project suggestions ← New
│   │   └── tn_automotive_taxonomy.py   # TN skill taxonomy + NSQF ← New
│   ├── main.py                         # FastAPI app & all endpoints
│   ├── models.py                       # Pydantic request/response models
│   ├── config.py                       # App configuration
│   └── requirements.txt
│
└── frontend/resume-frontend/
    ├── src/
    │   ├── components/
    │   │   ├── JobSearch.js
    │   │   ├── JobMatches.js
    │   │   ├── SkillAssessmentDashboard.js
    │   │   ├── Roadmapview.js              # Roadmap UI       ← New
    │   │   ├── ProjectSuggestions.js       # Project cards UI ← New
    │   │   └── TNAnalyticsDashboard.js     # Institution UI   ← New
    │   ├── App.js
    │   └── index.js
    └── package.json
```

---

## API Reference

### Resume

```http
POST /upload-resume/parse
Content-Type: multipart/form-data
```

### Job Matching

```http
POST /rag/match-realtime
Content-Type: application/json
```

### Roadmap Generation

```http
POST /generate/roadmap
Content-Type: application/json

{
  "resume_text": "...",
  "target_role": "Senior ML Engineer",
  "skill_gaps": ["kubernetes", "mlops", "system design"],
  "duration_weeks": 12,
  "experience_level": "mid"
}
```

```json
{
  "status": "success",
  "roadmap": {
    "title": "12-Week Path to Senior ML Engineer",
    "phases": [...],
    "total_hours_estimated": 120,
    "final_milestone": "...",
    "tips": [...]
  }
}
```

### Project Suggestions

```http
POST /generate/projects
Content-Type: application/json

{
  "resume_text": "...",
  "target_role": "Senior ML Engineer",
  "skill_gaps": ["kubernetes", "mlops"],
  "difficulty": "intermediate",
  "num_projects": 5
}
```

### TN Automotive — Single Profile *(New)*

```http
POST /tn/analyze-profile
Content-Type: application/json

{
  "profile_text": "ITI electrician. BMS training. HV safety certified...",
  "target_role": "EV Technician"
}
```

```json
{
  "extracted_skills": [...],
  "total_skills_found": 4,
  "nsqf_summary": {
    "peak_level": 4,
    "peak_label": "NSQF Level 4",
    "distribution": { "NSQF Level 3": [...], "NSQF Level 4": [...] }
  },
  "role_analysis": {
    "overall_match_pct": 75.0,
    "nsqf_current": 4,
    "nsqf_target": 4,
    "nsqf_gap": 0,
    "matched_required": ["Battery Management System (BMS)", "High Voltage Safety (HV Safety)"],
    "skill_gaps": [...],
    "typical_employers": ["Ola Electric", "TVS Motor", "TATA Motors"]
  }
}
```

### TN Automotive — Batch Analytics *(New)*

```http
POST /tn/batch-analytics
Content-Type: application/json

{
  "institution_name": "Government ITI Chennai – Auto & EV Batch 2025",
  "profiles": [
    { "id": "S001", "name": "Arjun K", "target_role": "EV Technician", "text": "..." },
    { "id": "S002", "name": "Priya L", "target_role": "CNC Operator",  "text": "..." }
  ]
}
```

```json
{
  "institution": "Government ITI Chennai – Auto & EV Batch 2025",
  "total_profiles": 2,
  "cohort_summary": {
    "avg_skills_per_person": 3.5,
    "nsqf_distribution": { "1": 0, "2": 0, "3": 1, "4": 1, "5": 0, "6": 0, "7": 0 },
    "top_skill_gaps": [
      { "skill": "CAN Bus / Automotive Communication Protocols", "count": 2, "pct": 100.0 }
    ],
    "top_skills_present": [...],
    "avg_role_readiness": { "EV Technician": 75.0, "CNC Operator": 50.0 }
  },
  "individual_results": [...]
}
```

### TN Taxonomy Metadata *(New)*

```http
GET /tn/roles      # All TN job roles with required skills and clusters
GET /tn/skills     # Full skill taxonomy with NSQF levels and training sources
```

### System

```http
GET /health
GET /config
GET /rag/stats
```

---

## TN Automotive Module

The TN AUTO SkillBridge module addresses **Track F: SkillTech & Workforce Analytics** for the Tamil Nadu automotive and EV ecosystem.

### Covered Skill Domains

| Domain | Skills |
|--------|--------|
| **EV Systems** | Battery Management System (BMS), Electric Motor & Drive, CAN Bus, EV Charging, HV Safety, Thermal Management |
| **Manufacturing** | CNC Operation, PLC Programming, Welding (MIG/TIG/Spot), Quality Control (IATF 16949), CAD/SolidWorks, Lean/5S |
| **Automation** | Robotics, Hydraulics & Pneumatics, Sheet Metal & Press Shop |
| **Digital** | Embedded C, IoT & Industry 4.0, Data Analysis & Python, ERP/SAP |
| **Common** | English Communication & Soft Skills |

### Supported Job Roles (TN Clusters)

| Role | Cluster | NSQF Target |
|------|---------|-------------|
| EV Technician | Chennai / Hosur / Coimbatore | Level 4 |
| CNC Operator | Hosur / Coimbatore / Chennai | Level 4 |
| Automation / PLC Engineer | Chennai / Hosur | Level 5 |
| Quality Inspector (Automotive) | Chennai / Hosur / Coimbatore | Level 4 |
| Battery Pack Assembler | Hosur / Chennai | Level 3 |
| Embedded Systems Engineer | Chennai | Level 6 |
| Production / Maintenance Technician | Chennai / Hosur / Coimbatore | Level 4 |

### Institutional Alignment

| Program | Integration |
|---------|-------------|
| Naan Mudhalvan | EV, Automation, IoT, CAD/CAM, Data Science modules |
| TNSDC EV Skill Centre | EV Technician track |
| SIEMENS Skill Centre TN | PLC, Robotics, Industry 4.0 |
| Government ITI / Polytechnic | CNC, Welding, Hydraulics, Electrical |
| NTTF Hosur | CNC, Machining |
| KUKA College Chennai | Robotics |
| BOSCH Training Centre Chennai | HV Safety, Automotive Service |

---

## Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | Job search API key | ✅ | — |
| `ANTHROPIC_API_KEY` | Claude API key | ✅ | — |
| `CLAUDE_MODEL` | Claude model version | | `claude-sonnet-4-20250514` |
| `EMBEDDING_MODEL` | Sentence transformer | | `all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIR` | ChromaDB path | | `./chroma_db` |
| `MAX_TOKENS_CAREER_ADVICE` | Token cap for advice | | `2000` |
| `MAX_TOKENS_ROADMAP` | Token cap for roadmaps | | `3000` |

**Frontend:** Update `API_BASE_URL` in `App.js` and components if your backend runs on a different port:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

---

## Example Output

### Match Score
```
Overall Match: 85%
├─ Semantic Similarity:  42/50
├─ Matched Skills:       35/40
└─ Skill Gap Penalty:    -7/20
Recommendation: Excellent Match ⭐
```

### Skill Assessment
```
✅ Matched Skills (8)
  Python      · Expert       · 5 yrs
  React       · Proficient   · 3 yrs
  AWS         · Intermediate · 2 yrs

⚠️ Skill Gaps (3)
  Kubernetes  · None → Intermediate  [Critical]
  GraphQL     · None → Beginner      [Moderate]

🌟 Bonus Skills (5)
  Django · PostgreSQL · Redis · Celery · Pytest
```

### Generated Roadmap (excerpt)
```
8-Week Path to Mid-Level Data Scientist

Phase 1 — Foundations (Weeks 1–2)
  Week 1: SQL & Data Wrangling
    Resources : Mode SQL Tutorial · Kaggle Pandas course
    Milestone : 3 Kaggle datasets cleaned end-to-end

  Week 2: Machine Learning Fundamentals
    Resources : fast.ai Part 1 · Hands-On ML (Ch. 1–6)
    Milestone : Train & evaluate 3 classification models

Phase 2 — Applied ML (Weeks 3–5)
  ...

Final Milestone: Deploy a full ML pipeline as a REST API with monitoring
```

### TN Batch Analytics (excerpt)
```
Institution: Government ITI Chennai – Auto & EV Batch 2025
Students Analyzed: 10  |  Avg Skills/Student: 3.2

NSQF Distribution
  Level 3 (Skilled / ITI):   3 students  (30%)
  Level 4 (Technician):      5 students  (50%)
  Level 6 (Jr. Engineer):    2 students  (20%)

Role Readiness
  EV Technician           → 58% avg  ⚠️ Needs short course
  CNC Operator            → 72% avg  ✅ Job-ready
  Embedded Systems Eng.   → 45% avg  ⚠️ Needs training

Top 3 Skill Gaps
  1. CAN Bus / Automotive Protocols  — 8/10 students (80%)  🔴 Critical
  2. Thermal Management in EVs       — 6/10 students (60%)  🟠 High
  3. IoT & Industry 4.0              — 5/10 students (50%)  🟠 High

Recommended Action Plan
  1. Run CAN Bus short-course — impacts 8 students (Naan Mudhalvan / Vector Academy)
  2. Schedule EV Thermal module — impacts 6 students (ARAI Online / IIT Madras)
  3. Add IoT module — impacts 5 students (SIEMENS Skill Centre TN)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Tailwind CSS |
| Backend | FastAPI, Python 3.8+ |
| AI / LLM | Anthropic Claude Sonnet 4 |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Job Search | SerpAPI (Google Jobs) |
| Resume Parsing | pdfplumber, python-docx |
| TN Taxonomy | Custom NSQF-mapped skill database |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Anthropic](https://anthropic.com) — Claude AI
- [SerpAPI](https://serpapi.com) — Job search data
- [ChromaDB](https://trychroma.com) — Vector storage
- [Sentence Transformers](https://sbert.net) — Embeddings
- [FastAPI](https://fastapi.tiangolo.com) & [React](https://reactjs.org) — Framework foundations
- [Naan Mudhalvan](https://naanmudhalvan.tn.gov.in) — TN skill development curriculum alignment
- [TNSDC](https://tnsdc.in) — Tamil Nadu Skill Development Corporation
- [ACMA](https://acma.in) — Automotive Component Manufacturers Association

---

<div align="center">
Built for <strong>Track F: SkillTech & Workforce Analytics</strong> · TN AUTO Skills Integration · Tamil Nadu Automotive & EV Ecosystem
</div>