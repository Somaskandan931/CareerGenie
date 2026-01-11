# Career Genie RAG

**Real-Time Resume-to-Job Matching using Retrieval-Augmented Generation**

Match resumes to live job postings with explainable AI, skill gap analysis, and direct apply links.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env and add your API keys:
# - SERPAPI_KEY (get from https://serpapi.com)
# - ANTHROPIC_API_KEY (get from https://anthropic.com)
```

### 3. Run Server
```bash
uvicorn main:app --reload
```

Server: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

---

## API Usage

### Real-Time Job Matching

```bash
POST /rag/match-realtime
```

**Request:**
```json
{
  "resume_text": "ML engineer with Python, TensorFlow, 3 years experience",
  "job_query": "machine learning engineer",
  "location": "India",
  "num_jobs": 50,
  "top_k": 10,
  "use_cache": true
}
```

**Response:**
```json
{
  "matched_jobs": [
    {
      "title": "ML Engineer",
      "company": "Flipkart",
      "match_score": 78.5,
      "matched_skills": ["Python", "ML", "TensorFlow"],
      "missing_required_skills": ["Docker"],
      "explanation": "Strong match based on your ML experience...",
      "recommendation": "Recommended - Good fit",
      "apply_link": "https://careers.flipkart.com/..."
    }
  ],
  "jobs_fetched": 50,
  "total_matches": 10,
  "cache_used": false
}
```

---

## Architecture

```
Resume Upload + Job Query
         ↓
Fetch Live Jobs (SerpAPI)
         ↓
Auto-Index to Vector DB (ChromaDB)
         ↓
Semantic Search
         ↓
RAG Reasoning (Claude)
         ↓
Explainable Matches
```

---

## Features

- **Real-Time Jobs**: Fetch live postings from Google Jobs
- **Auto Skill Extraction**: Detect skills from job descriptions
- **Vector Search**: Semantic matching with embeddings
- **RAG Explanations**: Evidence-backed match reasoning
- **Skill Gap Analysis**: Show matched and missing skills
- **Direct Apply Links**: One-click job applications
- **Intelligent Caching**: 24-hour cache for performance

---

## Performance

| Metric | Value |
|--------|-------|
| First Query | 8-15s |
| Cached Query | 2-3s |
| Jobs per Query | 50+ |
| Cache Duration | 24 hours |
| Match Accuracy | 78%+ |

---

## Testing

```bash
python test_realtime_rag.py
```

---

## Project Structure

```
career-genie-rag/
├── backend/
│   ├── rag/              # RAG system
│   │   ├── vector_store.py
│   │   ├── matcher.py
│   │   ├── job_scraper.py
│   │   └── router.py
│   ├── parser/           # Resume parsing
│   ├── builder/          # Resume generation
│   └── job_search/       # Legacy search
├── main.py               # FastAPI app
├── requirements.txt
├── .env
└── README.md
```

---

## 🔑 Environment Variables

```bash
SERPAPI_KEY=your_key          # For real-time job fetching
ANTHROPIC_API_KEY=your_key    # For RAG explanations
```

---

## API Endpoints

- `POST /rag/match-realtime` - Real-time job matching
- `GET /rag/stats` - Vector store statistics
- `POST /upload-resume/parse` - Parse resume
- `POST /build-resume` - Generate resume PDF
- `POST /search-jobs` - Legacy job search

---

## Example Usage

### Python
```python
import requests

response = requests.post("http://localhost:8000/rag/match-realtime", json={
    "resume_text": "Python developer with Django, 2 years",
    "job_query": "python developer",
    "location": "Bangalore",
    "num_jobs": 30,
    "top_k": 5
})

jobs = response.json()["matched_jobs"]
for job in jobs:
    print(f"{job['title']} - Score: {job['match_score']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/rag/match-realtime \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"ML engineer","job_query":"machine learning","location":"India","num_jobs":20,"top_k":5}'
```

---

## How It Works

### 1. Retrieval
Fetches 50+ live jobs from Google Jobs via SerpAPI based on your query.

### 2. Augmentation
Auto-extracts skills, indexes jobs to ChromaDB with semantic embeddings.

### 3. Generation
Uses Claude to generate evidence-backed match explanations citing specific job requirements.

**Result**: Explainable matches with skill gaps, recommendations, and apply links.

---

## Scaling

For production:
- Use Redis for distributed caching
- Implement rate limiting
- Add background job processing
- Set up monitoring/logging

---

## Troubleshooting

**Server won't start**
```bash
pip install -r requirements.txt --force-reinstall
```

**No jobs found**
```bash
# Check API key
cat .env | grep SERPAPI_KEY

# Try broader query
"job_query": "engineer"  # Instead of very specific
```

**Slow responses**
```bash
# Enable cache
"use_cache": true

# Reduce jobs
"num_jobs": 20  # Instead of 100
```

---

## License

MIT License

---

## Credits

Built with:
- FastAPI
- ChromaDB
- Sentence Transformers
- Anthropic Claude
- SerpAPI

---

**Ready to match resumes?**