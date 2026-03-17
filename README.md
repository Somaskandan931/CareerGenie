# Career Genie

## Overview

Career Genie is a modular AI-driven career intelligence platform that combines retrieval-augmented generation (RAG), agent-based AI systems, and workforce analytics to assist users in becoming job-ready.

The system goes beyond traditional job recommendation tools by integrating semantic job matching, AI-based career coaching, interview preparation, and skill gap analysis into a unified platform.

---

## Key Features

### AI Career Copilot
- Job Coach: Conversational assistant for career guidance and resume feedback
- Interview Coach: AI-generated mock interviews with contextual questions
- Market Insights: Skill demand analysis based on current trends
- Career Advisor: Personalized recommendations based on user profile

### Job Matching Engine
- Semantic job matching using vector embeddings
- Resume-based skill extraction with proficiency scoring
- Context-aware match explanations

### Learning and Development
- Automated roadmap generation based on skill gaps
- Project recommendations for portfolio building

### Job Intelligence Layer
- Real-time job retrieval using external APIs
- Job filtering and quality scoring
- Scam detection and validation

### TN SkillBridge Analytics
- NSQF-aligned skill taxonomy
- Role readiness evaluation
- Batch-level analytics for institutions

---

## System Design Overview

Career Genie follows a modular multi-engine architecture:

### 1. RAG Matching Engine
- Vector search using ChromaDB
- Embedding-based semantic retrieval
- Resume parsing and skill extraction

### 2. AI Copilot Agents
- Job Coach (chat-based assistant)
- Interview Coach (mock interview system)
- Market Insights (trend analysis)
- Career Advisor (decision support)

### 3. Generation Engines
- Roadmap Generator (learning paths)
- Project Generator (portfolio development)

### 4. Job Intelligence Layer
- Job scraping via external APIs
- Filtering and ranking logic
- Match scoring system

### 5. TN SkillBridge Engine
- Domain-specific taxonomy mapping
- Skill classification and analytics

---

## System Architecture

```
Frontend (React)
├── Job Matching Interface
├── Learning and Roadmaps
├── AI Coach Chat
├── Interview Simulator
├── Market Insights
└── Institution Dashboard
│
▼
FastAPI Backend (API Layer)
│
┌────────┼────────┬───────────────┬──────────────┬──────────────┐
▼        ▼        ▼               ▼              ▼

RAG Engine   AI Copilot   Generation    Job Layer   TN Analytics
(matcher)    Services     Engines       Engine      Engine

│            │             │             │             │
▼            ▼             ▼             ▼             ▼

ChromaDB   LLM APIs     Structured    External     Skill Taxonomy
Embeddings Context AI   Outputs       Job APIs     NSQF Mapping
```
### Backend Architecture

The backend is designed as a **modular AI platform** consisting of multiple specialized engines:

---

### 1. RAG Engine (Core Matching System)

**Files:**
- `matcher.py`
- `vector_store.py`
- `enhanced_skill_extractor.py`

**Responsibilities:**
- Semantic job matching using ChromaDB
- Resume-based skill extraction with proficiency scoring
- Match scoring and ranking logic

---

### 2. AI Copilot Layer (Agentic AI)

**Files:**
- `job_coach.py`
- `interview_coach.py`
- `market_insights.py`
- `career_advisor.py`

**Responsibilities:**
- Conversational career guidance (Job Coach)
- AI-powered mock interviews (Interview Coach)
- Skill demand and trend analysis (Market Insights)
- Personalized career recommendations (Career Advisor)

This layer transforms the system into an **agent-based AI platform**, enabling interactive and context-aware assistance.

---

### 3. Generation Engines

**Files:**
- `roadmap_generator.py`
- `project_generator.py`

**Responsibilities:**
- Generate personalized learning roadmaps
- Suggest portfolio-building projects
- Structured outputs using LLM-based reasoning

---

### 4. Job Intelligence Layer

**Files:**
- `job_scraper.py`
- `job_filter.py`

**Responsibilities:**
- Job data retrieval using external APIs (SerpAPI)
- Scam detection and filtering
- Job quality scoring and ranking

---

### 5. TN SkillBridge Engine (Domain Intelligence)

**Files:**
- `tn_automotive_taxonomy.py`

**Responsibilities:**
- NSQF-based skill taxonomy mapping
- Role readiness evaluation
- Batch-level analytics for institutions

---

### Summary

This modular design enables:
- Independent scaling of components
- Clear separation of responsibilities
- Integration of RAG, Agentic AI, and analytics in a single platform

---

## RAG Pipeline



User Resume + Job Query
│
▼

1. Parse and Extract

   * Resume parsing
   * Skill extraction
   * Proficiency scoring

2. Retrieve

   * Semantic search using embeddings
   * Vector database lookup

3. Augment

   * Resume context
   * Job description
   * Skill gaps
   * Market insights

4. Generate

   * Job match explanations
   * Career advice
   * Learning roadmap
   * Project suggestions
   * Interview questions

5. Feedback Loop

   * User interaction via AI Copilot
   * Continuous refinement of outputs



---

## Technology Stack

| Layer        | Technology Used                     |
|-------------|------------------------------------|
| Frontend     | React, Tailwind CSS                |
| Backend      | FastAPI                            |
| Vector DB    | ChromaDB                           |
| Embeddings   | Sentence Transformers (MiniLM)     |
| AI/LLM       | Groq (Primary LLM Inference)       |
| Job Data     | External APIs (SerpAPI)            |
| Storage      | JSON / Local Config                |

---

## Multi-Tab User Interface

The frontend is organized into modular functional tabs:

| Tab           | Description |
|--------------|------------|
| Job Matches   | Resume-based semantic job matching |
| Learning      | Roadmaps and project generation |
| Job Coach     | Conversational AI assistant |
| Insights      | Market trend analysis |
| Interview     | Mock interview system |
| Institution   | TN SkillBridge analytics dashboard |

---

## Intelligent Backend Features

- Dynamic configuration validation via API endpoints
- Modular service-based architecture
- Adaptive skill gap detection
- Multi-model AI integration
- Scalable design for additional AI services

---

## AI Architecture Paradigm

Career Genie follows a hybrid AI approach:

- Retrieval-Augmented Generation (RAG) for accurate job matching
- Agent-based AI systems for interactive guidance
- Generative pipelines for structured outputs such as roadmaps and projects

This design enables both high precision and contextual reasoning.

---

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
````

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## Future Enhancements

* Multi-language support
* Real-time interview voice interaction
* Advanced personalization using user history
* Deployment-ready cloud architecture
* Integration with professional networking platforms



