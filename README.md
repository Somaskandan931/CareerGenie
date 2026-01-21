# Career Genie 

![Career Genie Banner](https://img.shields.io/badge/AI-Powered-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![React](https://img.shields.io/badge/React-18+-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

**AI-Powered Job Discovery with Skill Gap Analysis & Personalized Learning Paths**

Career Genie is an intelligent career platform that uses RAG (Retrieval Augmented Generation) and AI to match your resume with relevant jobs, identify skill gaps, and provide personalized career guidance.

---

##  Features

### **Smart Job Matching**
- **RAG-Powered Matching**: Uses vector embeddings and semantic search to find jobs that match your skills and experience
- **Real-time Job Search**: Scrapes live jobs from Google Jobs via SerpAPI
- **AI-Generated Explanations**: Claude AI explains why each job is a good match for you
- **Match Scoring**: Get detailed match scores (0-100%) with skill breakdowns

###  **Skill Assessment Dashboard**
- **Visual Skill Analysis**: See your skills categorized and scored
- **Matched Skills**: Identify which of your skills align with job requirements
- **Skill Gaps**: Discover critical skills you need to develop
- **Bonus Skills**: Highlight additional skills that make you stand out

###  **Career Guidance**
- **Personalized Career Advice**: AI-generated assessment of your current position
- **Learning Path Recommendations**: Curated courses and resources for skill development
- **Career Progression Roadmap**: Clear timeline from entry-level to senior roles
- **Market Insights**: Current salary expectations and industry trends
- **Actionable Plans**: Step-by-step actions for career advancement

###  **Advanced Filtering**
- Filter by experience level (Entry/Mid/Senior)
- Minimum match score threshold
- Job posting recency (7/14/30/60 days)
- Remote/on-site preferences
- Quality scoring to avoid scam listings

---

##  Architecture

```
┌─────────────────┐
│   React Frontend│
│   (Tailwind CSS)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│
│                 │
├─────────────────┤
│ • Resume Parser │
│ • Job Scraper   │
│ • Vector Store  │
│ • AI Matcher    │
│ • Career Advisor│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  External Services          │
├─────────────────────────────┤
│ • SerpAPI (Job Search)      │
│ • Claude AI (Matching)      │
│ • ChromaDB (Vector Storage) │
│ • Sentence Transformers     │
└─────────────────────────────┘
```

### **RAG Pipeline**

1. **Retrieval**: Semantic search finds relevant jobs using vector embeddings
2. **Augmentation**: Context includes resume, job description, and matched skills
3. **Generation**: Claude AI generates personalized explanations and career advice

---

##  Getting Started

### **Prerequisites**

- Python 3.8+
- Node.js 16+
- npm or yarn

### **API Keys Required**

1. **SerpAPI Key**: For job searching
   - Sign up at [serpapi.com](https://serpapi.com/)
   - Free tier: 100 searches/month

2. **Anthropic API Key**: For AI-powered matching and career advice
   - Sign up at [console.anthropic.com](https://console.anthropic.com/)
   - Get API key from settings

---

## Installation

### **1. Clone the Repository**

```bash
git clone https://github.com/somaskandan931/career-genie.git
cd career-genie
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
SERPAPI_KEY=your_serpapi_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_db
MAX_TOKENS_CAREER_ADVICE=2000
EOL

# Run the backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### **3. Frontend Setup**

```bash
cd frontend/resume-frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

---

##  Usage

### **Step 1: Upload Your Resume**
- Click "Upload Resume" and select your PDF or DOCX file
- The system will parse and extract your skills

### **Step 2: Search for Jobs**
- Enter job title/keywords (e.g., "Software Engineer", "Data Scientist")
- Set location (e.g., "India", "Bangalore", "Remote")
- Apply advanced filters:
  - Experience Level
  - Minimum Match Score
  - Job Recency
  - Remote Preferences

### **Step 3: Review Matches**
- View AI-generated match scores and explanations
- See matched skills and skill gaps for each job
- Get personalized recommendations

### **Step 4: Get Career Guidance**
- Review your skill assessment dashboard
- Explore learning resources for skill development
- Follow the career progression roadmap
- Read market insights and action plans

---

##  Tech Stack

### **Backend**
- **FastAPI**: Modern, fast web framework
- **Anthropic Claude**: AI-powered matching and career advice
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Text embeddings
- **SerpAPI**: Real-time job scraping
- **pdfplumber & python-docx**: Resume parsing

### **Frontend**
- **React**: UI framework
- **Tailwind CSS**: Utility-first styling
- **Fetch API**: Backend communication

### **AI/ML**
- **RAG Architecture**: Retrieval Augmented Generation
- **Semantic Search**: Vector similarity matching
- **Claude Sonnet 4**: Advanced language model
- **all-MiniLM-L6-v2**: Embedding model

---

## Project Structure

```
career-genie/
├── backend/
│   ├── services/
│   │   ├── career_advisor.py       # AI career guidance
│   │   ├── enhanced_skill_extractor.py  # Advanced skill extraction
│   │   ├── job_filter.py           # Smart job filtering
│   │   ├── job_scraper.py          # SerpAPI job scraping
│   │   ├── matcher.py              # RAG-based matching
│   │   ├── resume_parser.py        # PDF/DOCX parsing
│   │   └── vector_store.py         # ChromaDB integration
│   ├── main.py                     # FastAPI application
│   ├── models.py                   # Pydantic models
│   ├── config.py                   # Configuration
│   └── requirements.txt            # Python dependencies
│
├── frontend/resume-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── JobSearch.js        # Job search interface
│   │   │   ├── JobMatches.js       # Match results display
│   │   │   └── SkillAssessmentDashboard.js  # Skill visualization
│   │   ├── App.js                  # Main application
│   │   └── index.js                # Entry point
│   ├── public/
│   └── package.json                # Node dependencies
│
└── README.md
```

---

## Configuration

### **Backend Environment Variables**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | SerpAPI key for job search | Yes | - |
| `ANTHROPIC_API_KEY` | Claude API key | Yes | - |
| `CLAUDE_MODEL` | Claude model version | No | `claude-sonnet-4-20250514` |
| `EMBEDDING_MODEL` | Sentence transformer model | No | `all-MiniLM-L6-v2` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | No | `./chroma_db` |
| `MAX_TOKENS_CAREER_ADVICE` | Max tokens for career advice | No | `2000` |

### **Frontend Configuration**

Update `API_BASE_URL` in components if backend runs on a different port:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

---

##  API Endpoints

### **Resume Operations**
```http
POST /upload-resume/parse
Content-Type: multipart/form-data

Response: {
  status: "success",
  resume_text: "...",
  word_count: 450
}
```

### **Job Matching**
```http
POST /rag/match-realtime
Content-Type: application/json

{
  "resume_text": "...",
  "job_query": "software engineer",
  "location": "India",
  "num_jobs": 50,
  "top_k": 10,
  "min_match_score": 40,
  "experience_level": "mid",
  "posted_within_days": 14,
  "exclude_remote": false
}

Response: {
  "matched_jobs": [...],
  "career_advice": {...},
  "skill_comparison": {...},
  "total_jobs_fetched": 50,
  "total_jobs_indexed": 48
}
```

### **System Status**
```http
GET /config
GET /health
GET /rag/stats
```

---

##  Features in Detail

### **1. Smart Job Filtering**
- **Quality Scoring**: Filters out scam jobs and low-quality listings
- **Red Flags**: Detects "work from home scams", "MLM", etc.
- **Quality Indicators**: Rewards listings with benefits, training, career growth

### **2. Enhanced Skill Extraction**
- **Context-Aware**: Understands skill proficiency from surrounding text
- **Multi-Level**: Detects beginner, intermediate, proficient, expert levels
- **Experience Extraction**: Parses years of experience (e.g., "5+ years Python")

### **3. RAG-Powered Matching**
- **Semantic Search**: Finds jobs beyond keyword matching
- **Hybrid Scoring**: Combines semantic similarity + skill matching
- **AI Explanations**: Claude generates personalized match reasons

### **4. Career Progression Paths**
- **Role Timeline**: Entry → Mid → Senior level transitions
- **Skill Requirements**: What you need at each stage
- **Responsibilities**: Typical duties for each role

---

## Example Output

### **Match Score Breakdown**
```
Overall Match: 85%
├─ Semantic Similarity: 42/50 points
├─ Matched Skills: 35/40 points
└─ Missing Skills Penalty: -7/20 points

Recommendation: Excellent Match
```

### **Skill Assessment**
```
   Matched Skills (8):
   Python (Expert, 5 years) ★
   React (Proficient, 3 years) ★
   AWS (Intermediate, 2 years) ★

 Skill Gaps (3):
   Kubernetes: None → Intermediate [Critical]
   GraphQL: None → Beginner [Moderate]
   
 Bonus Skills (5):
   Django (Advanced)
   PostgreSQL (Proficient)
```


---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Anthropic Claude**: For powerful AI capabilities
- **SerpAPI**: For reliable job search data
- **ChromaDB**: For efficient vector storage
- **Sentence Transformers**: For quality embeddings
- **FastAPI & React**: For excellent developer experience

