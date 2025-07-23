from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.builder.router import router as builder_router
from backend.parser.router import router as parser_router
from backend.job_search.router import router as job_router
from backend.matcher.router import router as matcher_router

app = FastAPI(
    title="CareerGenie Resume Backend",
    description="Resume builder and parser API for CareerGenie",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(builder_router, prefix="/builder", tags=["builder"])
app.include_router(parser_router, prefix="/upload-resume", tags=["parser"])
app.include_router(job_router, prefix="/search-jobs", tags=["jobs"])
app.include_router(matcher_router, prefix="/match-jobs", tags=["matcher"])

@app.get("/")
def root():
    return {"message": "CareerGenie backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}