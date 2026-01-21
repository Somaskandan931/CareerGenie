from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import logging
from pathlib import Path

# Import configuration first
from backend.config import settings

# Import models
from backend.models import (
    ResumeUploadResponse,
    JobMatchRequest,
    JobMatchResponse,
    ConfigResponse,
    JobMatch,
)

# Import services
from backend.services.resume_parser import resume_parser
from backend.services.vector_store import vector_store
from backend.services.matcher import get_job_matcher
from backend.services.career_advisor import career_advisor
from backend.services.job_scraper import get_job_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger( __name__ )

# Create FastAPI app
app = FastAPI(
    title="Career Genie RAG",
    description="AI-powered job matching using RAG (Retrieval Augmented Generation)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CONFIGURATION ENDPOINT
# ============================================================================

@app.get( "/config", response_model=ConfigResponse )
def get_config () :
    """Check backend configuration and status"""
    return ConfigResponse(
        serpapi_key_present=bool( settings.SERPAPI_KEY ),
        searchapi_key_present=bool( settings.SERPAPI_KEY ),
        anthropic_key_present=bool( settings.ANTHROPIC_API_KEY ),
        vector_db_initialized=True,
        total_indexed_jobs=vector_store.collection.count()
    )


# ============================================================================
# RESUME PARSING ENDPOINT
# ============================================================================

@app.post( "/upload-resume/parse", response_model=ResumeUploadResponse )
async def parse_resume ( file: UploadFile = File( ... ) ) :
    """Parse uploaded resume (PDF or DOCX)"""
    logger.info( f"Received resume upload: {file.filename}" )

    # Validate file type
    if not file.filename.lower().endswith( ('.pdf', '.docx', '.doc') ) :
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload PDF or DOCX file."
        )

    # Save to temporary file
    suffix = Path( file.filename ).suffix
    with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as tmp :
        content = await file.read()
        tmp.write( content )
        temp_path = tmp.name

    try :
        # Parse resume
        result = resume_parser.parse( temp_path )

        logger.info( f"Successfully parsed resume: {result['word_count']} words" )

        return ResumeUploadResponse(
            status="success",
            resume_text=result['resume_text'],
            word_count=result['word_count']
        )

    except Exception as e :
        logger.error( f"Error parsing resume: {str( e )}" )
        raise HTTPException( status_code=500, detail=f"Failed to parse resume: {str( e )}" )

    finally :
        # Clean up temp file
        if os.path.exists( temp_path ) :
            try :
                os.remove( temp_path )
            except Exception as e :
                logger.warning( f"Failed to remove temp file: {str( e )}" )


# ============================================================================
# RAG JOB MATCHING ENDPOINT (WITH CAREER ADVICE & FILTERS)
# ============================================================================

@app.post( "/rag/match-realtime", response_model=JobMatchResponse )
def match_jobs_realtime ( request: JobMatchRequest ) :
    """
    RAG-powered job matching with career advice and smart filtering:
    1. Scrape jobs from Google Jobs
    2. Apply smart filters (quality, experience, recency)
    3. Index jobs in vector database
    4. Semantic search for relevant jobs
    5. Use Claude to generate match explanations
    6. Generate personalized career advice
    """
    logger.info( f"Job match request: query='{request.job_query}', location='{request.location}'" )
    logger.info(
        f"Filters: min_score={request.min_match_score}, exp_level={request.experience_level}, days={request.posted_within_days}" )

    # Validate inputs
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="Resume text is required" )

    if not request.job_query.strip() :
        raise HTTPException( status_code=400, detail="Job query is required" )

    try :
        # Step 1: Scrape jobs
        logger.info( "Step 1: Scraping jobs..." )
        jobs = get_job_scraper().fetch_jobs(
            query=request.job_query,
            location=request.location,
            num_jobs=request.num_jobs
        )

        if not jobs :
            logger.warning( "No jobs found from scraper, returning empty result" )
            return JobMatchResponse(
                matched_jobs=[],
                total_jobs_fetched=0,
                total_jobs_indexed=0,
                search_query=f"{request.job_query} in {request.location}",
                career_advice=None
            )

        # Step 2: Apply smart filtering (optional - only if job_filter.py exists)
        try :
            from backend.services.job_filter import SmartJobFilter
            logger.info( "Step 2: Applying smart filters..." )
            filter_engine = SmartJobFilter()

            filtered_jobs = filter_engine.filter_jobs(
                jobs,
                min_match_score=request.min_match_score,
                experience_level=request.experience_level,
                posted_within_days=request.posted_within_days,
                exclude_remote=request.exclude_remote
            )

            logger.info( f"Filtered {len( jobs )} jobs down to {len( filtered_jobs )} quality matches" )
            jobs_to_index = filtered_jobs if filtered_jobs else jobs
        except ImportError :
            logger.warning( "SmartJobFilter not available, skipping filtering" )
            jobs_to_index = jobs

        # Step 3: Index jobs in vector database
        logger.info( "Step 3: Indexing jobs in vector database..." )
        indexed_count = vector_store.index_jobs( jobs_to_index )

        if indexed_count == 0 :
            raise HTTPException( status_code=500, detail="Failed to index jobs in vector database" )

        # Step 4: Match resume to jobs using RAG
        logger.info( "Step 4: Matching resume to jobs using RAG..." )
        matches = get_job_matcher().match_resume_to_jobs(
            resume_text=request.resume_text,
            top_k=request.top_k
        )

        # Step 5: Generate career advice
        logger.info( "Step 5: Generating career advice..." )
        career_advice_data = None
        if career_advisor is not None :
            try :
                career_advice_data = career_advisor.generate_career_advice(
                    resume_text=request.resume_text,
                    target_role=request.job_query,
                    current_role=None,
                    job_matches=matches[:3]
                )
                logger.info( "Career advice generated successfully" )
            except Exception as e :
                logger.error( f"Failed to generate career advice: {str( e )}" )
                # Continue without career advice
        else :
            logger.warning( "CareerAdvisor not initialized, skipping career advice" )

        # Step 6: Generate skill comparison for dashboard (optional)
        skill_comparison_data = None
        try :
            # Extract skills from resume and top job
            if matches :
                resume_skills_raw = get_job_matcher()._extract_skills( request.resume_text )
                job_skills_raw = get_job_matcher()._extract_skills( matches[0].get( 'description', '' ) )

                matched = list( set( resume_skills_raw ) & set( job_skills_raw ) )
                gaps = list( set( job_skills_raw ) - set( resume_skills_raw ) )
                bonus = list( set( resume_skills_raw ) - set( job_skills_raw ) )

                skill_comparison_data = {
                    "overall_match" : matches[0].get( 'match_score', 0 ) if matches else 0,
                    "matched_skills" : [{"skill" : s, "status" : "qualified"} for s in matched],
                    "skill_gaps" : [{"skill" : s, "resume_level" : "none", "required_level" : "intermediate",
                                     "gap_severity" : "moderate"} for s in gaps],
                    "bonus_skills" : [{"skill" : s} for s in bonus],
                    "resume_skills" : [{"skill" : s, "category" : "Programming"} for s in resume_skills_raw],
                    "job_skills" : [{"skill" : s, "category" : "Programming"} for s in job_skills_raw]
                }
        except Exception as e :
            logger.error( f"Failed to generate skill comparison: {str( e )}" )

        # Convert to response models
        job_matches = [JobMatch( **match ) for match in matches]

        response_data = {
            "matched_jobs" : job_matches,
            "total_jobs_fetched" : len( jobs ),
            "total_jobs_indexed" : indexed_count,
            "search_query" : f"{request.job_query} in {request.location}"
        }

        # Add career advice if available
        if career_advice_data :
            response_data["career_advice"] = career_advice_data

        # Add skill comparison if available
        if skill_comparison_data :
            response_data["skill_comparison"] = skill_comparison_data

        logger.info( f"Successfully matched {len( job_matches )} jobs" )

        return JobMatchResponse( **response_data )

    except HTTPException :
        raise

    except Exception as e :
        logger.error( f"Error in job matching: {str( e )}", exc_info=True )
        raise HTTPException( status_code=500, detail=f"Job matching failed: {str( e )}" )


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get( "/rag/stats" )
def get_stats () :
    """Get RAG system statistics"""
    return vector_store.get_stats()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get( "/health" )
def health_check () :
    """Health check endpoint"""
    errors = settings.validate()

    return {
        "status" : "healthy" if not errors else "degraded",
        "errors" : errors,
        "vector_db_jobs" : vector_store.collection.count(),
        "services" : {
            "vector_store" : "ok",
            "job_scraper" : "ok" if settings.SERPAPI_KEY else "missing_api_key",
            "career_advisor" : "ok" if career_advisor is not None else "not_initialized"
        }
    }


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event( "startup" )
async def startup_event () :
    """Validate configuration on startup"""
    logger.info( "=" * 60 )
    logger.info( "Starting Career Genie RAG API..." )
    logger.info( "=" * 60 )

    # Create necessary directories
    Path( settings.CHROMA_PERSIST_DIR ).mkdir( parents=True, exist_ok=True )

    errors = settings.validate()
    if errors :
        logger.error( "Configuration errors:" )
        for error in errors :
            logger.error( f"  ❌ {error}" )
        logger.warning( "⚠️  API started but some features may not work!" )
    else :
        logger.info( "✅ All configurations valid" )

    logger.info( f"✅ Vector store initialized with {vector_store.collection.count()} jobs" )
    logger.info( f"✅ Career advisor: {'Initialized' if career_advisor else 'Not initialized'}" )
    logger.info( "=" * 60 )


if __name__ == "__main__" :
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )