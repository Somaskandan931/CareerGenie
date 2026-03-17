<div align="center">

# Career Genie

**AI-Powered Job Discovery · Skill Gap Analysis · Personalized Learning Paths · Career Roadmaps**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Claude AI](https://img.shields.io/badge/Claude_AI-Sonnet_4-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-features) · [Architecture](#-architecture) · [Getting Started](#-getting-started) · [Usage](#-usage) · [API Reference](#-api-reference) · [Contributing](#-contributing)

</div>

---

## What is Career Genie?

Career Genie is an intelligent career platform that uses **RAG (Retrieval Augmented Generation)** to match your resume with live job listings, identify skill gaps, generate week-by-week learning roadmaps, and suggest hands-on projects — all powered by Claude AI.

Upload your resume → search for roles → get a personalized plan to land the job.

---

## Features

### Smart Job Matching
- **RAG-Powered Matching** — Vector embeddings and semantic search surface jobs that fit *your* experience, not just keyword matches
- **Real-time Job Search** — Pulls live listings from Google Jobs via SerpAPI
- **AI Match Explanations** — Claude tells you exactly *why* each job is a fit
- **Match Scoring** — Detailed 0–100% scores with per-skill breakdowns

### Skill Assessment Dashboard
- Visual skill categorisation and proficiency scoring
- **Matched Skills** — What you already bring to the table
- **Skill Gaps** — Critical skills to develop, ranked by importance
- **Bonus Skills** — Your differentiators beyond the job description

### Career Guidance
- AI-generated assessment of your current standing
- Curated learning paths with specific courses and resources
- Career progression roadmap: Entry → Mid → Senior
- Salary expectations, market insights, and actionable next steps

### Career Roadmaps & Projects
- **Personalised Roadmaps** — Week-by-week learning plans built from your actual skill gaps
- **Milestone Tracking** — Visual progress checkpoints you can mark complete
- **Hands-on Project Suggestions** — Curated projects with difficulty, time estimates, and tech stacks
- **Project Templates** — Starter code and GitHub-ready repos
- **Portfolio Builder** — Track completed projects and export a shareable summary
- **Export** — Download your roadmap as PDF or share via link

### Advanced Filtering
- Experience level: Entry / Mid / Senior
- Minimum match score threshold
- Job recency: 7 / 14 / 30 / 60 days
- Remote / on-site / hybrid preference
- Quality scoring to filter out scam listings

---

## Architecture

```
┌──────────────────────┐
│ React Frontend │
│ (Tailwind CSS) │
└──────────┬───────────┘
│ REST API
▼
┌──────────────────────┐
│ FastAPI Backend │
├──────────────────────┤
│ Resume Parser │
│ Job Scraper │
│ Vector Store │
│ AI Matcher │
│ Career Advisor │
│ Roadmap Generator │ ← New
│ Project Generator │ ← New
└──────────┬───────────┘
│
▼
┌────────────────────────────────┐
│ External Services │
├────────────────────────────────┤
│ SerpAPI (jobs) │
│ Claude Sonnet 4 (AI) │
│ ChromaDB (vectors) │
│ Sentence Transformers (embed) │
└────────────────────────────────┘
```

### RAG Pipeline

```
Resume + Job Description
│
▼
1. RETRIEVE → Semantic search over ChromaDB vector store
2. AUGMENT → Combine resume context + job desc + matched skills
3. GENERATE → Claude produces explanations, roadmaps, projects
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
source venv/bin/activate # Mac/Linux
# venv\Scripts\activate # Windows

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

## ‍ Usage

| Step | Action |
|------|--------|
| **1. Upload Resume** | Upload PDF or DOCX — system extracts skills automatically |
| **2. Search Jobs** | Enter title + location, apply filters (level, recency, remote) |
| **3. Review Matches** | See match scores, explanations, matched skills, and gaps |
| **4. Get Career Guidance** | Explore learning resources, roadmap, and market insights |
| **5. Generate Roadmap** | Click "Generate Roadmap" on any match for a personalised plan |
| **6. Track Progress** | Mark milestones complete, build your portfolio, export or share |

---

## Project Structure

```
career-genie/
├── backend/
│ ├── services/
│ │ ├── career_advisor.py # AI career guidance
│ │ ├── enhanced_skill_extractor.py # Proficiency-aware skill extraction
│ │ ├── job_filter.py # Quality scoring & scam filtering
│ │ ├── job_scraper.py # SerpAPI integration
│ │ ├── matcher.py # RAG-based job matching
│ │ ├── resume_parser.py # PDF/DOCX parsing
│ │ ├── vector_store.py # ChromaDB integration
│ │ ├── roadmap_generator.py # ← AI roadmap generation
│ │ └── project_generator.py # ← AI project suggestions
│ ├── main.py # FastAPI app entry point
│ ├── models.py # Pydantic request/response models
│ ├── config.py # App configuration
│ └── requirements.txt
│
└── frontend/resume-frontend/
├── src/
│ ├── components/
│ │ ├── JobSearch.js
│ │ ├── JobMatches.js
│ │ ├── SkillAssessmentDashboard.js
│ │ ├── RoadmapView.js # ← Roadmap UI
│ │ └── ProjectSuggestions.js # ← Project cards UI
│ ├── App.js
│ └── index.js
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

### Roadmap Generation *(New)*

```http
POST /roadmap/generate
Content-Type: application/json

{
"resume_text": "...",
"target_role": "Senior ML Engineer",
"skill_gaps": ["kubernetes", "mlops", "system design"],
"duration_weeks": 12
}
```

```json
{
"roadmap": {
"title": "12-Week Path to Senior ML Engineer",
"weeks": [...],
"milestones": [...],
"total_hours_estimated": 120
}
}
```

### Project Suggestions *(New)*

```http
POST /projects/suggest
Content-Type: application/json

{
"resume_text": "...",
"target_role": "Senior ML Engineer",
"skill_gaps": ["kubernetes", "mlops"],
"difficulty": "intermediate",
"num_projects": 5
}
```

### System

```http
GET /health
GET /config
GET /rag/stats
GET /roadmap/{roadmap_id}
POST /roadmap/{roadmap_id}/milestone/complete
```

---

## Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | Job search API key | | — |
| `ANTHROPIC_API_KEY` | Claude API key | | — |
| `CLAUDE_MODEL` | Claude model version | | `claude-sonnet-4-20250514` |
| `EMBEDDING_MODEL` | Sentence transformer | | `all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIR` | ChromaDB path | | `./chroma_db` |
| `MAX_TOKENS_CAREER_ADVICE` | Token cap for advice | | `2000` |
| `MAX_TOKENS_ROADMAP` | Token cap for roadmaps | | `3000` |

**Frontend:** Update `API_BASE_URL` in components if backend runs on a non-default port:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

---

## Example Output

**Match Score**
```
Overall Match: 85%
├─ Semantic Similarity: 42/50
├─ Matched Skills: 35/40
└─ Skill Gap Penalty: -7/20
Recommendation: Excellent Match 
```

**Skill Assessment**
```
Matched Skills (8)
Python Expert 5 yrs
React Proficient 3 yrs
AWS Intermediate 2 yrs

Skill Gaps (3)
Kubernetes None → Intermediate [Critical]
GraphQL None → Beginner [Moderate]

Bonus Skills (5)
Django · PostgreSQL · Redis · Celery · Pytest
```

**Generated Roadmap (excerpt)**
```
8-Week Path to Mid-Level Data Scientist

Week 1–2: SQL & Data Wrangling
Resources: Mode SQL Tutorial · Kaggle Pandas course
Milestone: 3 Kaggle datasets end-to-end

Week 3–4: Machine Learning Fundamentals
Resources: fast.ai Part 1 · Hands-On ML (Ch. 1–6)
Milestone: Train & evaluate 3 classification models

Week 5–6: MLOps & Deployment
Resources: MLflow quickstart · FastAPI docs
Milestone: Deploy a model as a REST API

Week 7–8: Portfolio Projects
→ Customer Churn Predictor
→ Salary Estimator with Explainability
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

---
