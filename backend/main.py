from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.builder.router import router as builder_router# NEW
from backend.parser.router import router as parser_router
from backend.job_search.router import router as job_router
from backend.matcher.router import router as matcher_router
app = FastAPI(
    title="CareerGenie Resume Backend",
    description="Resume builder and parser API for CareerGenie",
    version="1.0.0"
)

# ✅ Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include your routers
app.include_router(builder_router, prefix="/generate-latex")
app.include_router(parser_router, prefix="/upload-resume")
app.include_router(job_router, prefix="/search-jobs")
app.include_router(matcher_router, prefix="/match-jobs")
# ✅ Health check endpoint
@app.get("/")
def root():
    return {"message": "CareerGenie backend is running"}
