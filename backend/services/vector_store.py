import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict
import logging
import os
from pathlib import Path
from datetime import datetime
import numpy as np

# Disable ChromaDB telemetry
os.environ.setdefault( "ANONYMIZED_TELEMETRY", "False" )
os.environ.setdefault( "CHROMA_TELEMETRY", "False" )

from backend.core.config import settings

logger = logging.getLogger( __name__ )


class VectorStore :
    def __init__ ( self ) :
        """Initialize ChromaDB with lazy embedding loading"""
        # Ensure directory exists
        persist_dir = Path( settings.CHROMA_PERSIST_DIR )
        persist_dir.mkdir( parents=True, exist_ok=True )

        logger.info( f"Initializing ChromaDB at: {persist_dir}" )

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str( persist_dir ),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="job_listings",
            metadata={"description" : "Job listings for RAG matching"}
        )

        # Lazy-loaded embedder
        self.embedder = None
        self._dimension = 384  # TF-IDF max features dimension
        self._embedder_initialized = False
        self._use_tfidf = True  # Use TF-IDF on Render (memory efficient)
        self._tfidf_fitted = False  # Track whether TF-IDF has been fit
        self._tfidf_corpus: List[str] = []  # Corpus used to fit the vectorizer

        logger.info( f"Vector store initialized. Current jobs: {self.collection.count()}" )

    def _ensure_embedder ( self ) :
        """Load embedding model only when first needed. Prevents Render startup OOM."""
        if not self._embedder_initialized :
            logger.info( "Lazy-loading embedding model..." )
            self.embedder = self._init_embedder()
            self._embedder_initialized = True

    def _init_embedder ( self ) :
        """
        Initialize embedder - use TF-IDF for Render (memory efficient),
        or try Ollama/SentenceTransformer if available.
        """
        # Check if we're on Render (memory constrained)
        is_render = os.environ.get( "RENDER", "" ).lower() == "true"

        if is_render or self._use_tfidf :
            logger.warning( "Using lightweight TF-IDF embeddings (Render/constrained mode)" )
            from sklearn.feature_extraction.text import TfidfVectorizer
            return TfidfVectorizer(
                max_features=self._dimension,
                stop_words="english",
                lowercase=True,
                strip_accents="unicode"
            )

        # Try Ollama first (lightweight if available)
        try :
            from backend.services.ollama_service import get_ollama_service
            ollama_svc = get_ollama_service()
            if ollama_svc.available :
                logger.info( f"Using Ollama for embeddings (model: {ollama_svc.embedding_model})" )
                self._use_tfidf = False
                return ollama_svc
            logger.info( "Ollama not reachable — will use SentenceTransformer" )
        except Exception as e :
            logger.info( f"Ollama skipped ({e}) — will use SentenceTransformer" )

        # SentenceTransformer fallback (heavy - not recommended for Render)
        try :
            from sentence_transformers import SentenceTransformer
            model_name = getattr( settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2" )
            logger.info( f"Loading SentenceTransformer: {model_name}" )
            self._use_tfidf = False
            return SentenceTransformer( model_name )
        except Exception as e :
            logger.error( f"Failed to load SentenceTransformer: {e}" )
            # Final fallback to TF-IDF
            logger.warning( "Falling back to TF-IDF embeddings" )
            from sklearn.feature_extraction.text import TfidfVectorizer
            return TfidfVectorizer(
                max_features=self._dimension,
                stop_words="english"
            )

    def _get_embedding ( self, text: str ) -> List[float] :
        """Get embedding for a single text"""
        self._ensure_embedder()

        try :
            # Check if using Ollama service
            if hasattr( self.embedder, 'get_embedding' ) :
                embedding = self.embedder.get_embedding( text )
                if isinstance( embedding, np.ndarray ) :
                    return embedding.tolist()
                return embedding

            # Check if using TF-IDF
            if hasattr( self.embedder, 'transform' ) :
                # TF-IDF vectorizer — must be fitted before transform
                if not self._tfidf_fitted:
                    result = self.embedder.fit_transform( [text] ).toarray()[0]
                    self._tfidf_fitted = True
                    self._tfidf_corpus = [text]
                    return result.tolist()
                else:
                    try:
                        result = self.embedder.transform( [text] ).toarray()[0]
                        return result.tolist()
                    except Exception:
                        combined = self._tfidf_corpus + [text]
                        self.embedder.fit( combined )
                        self._tfidf_fitted = True
                        result = self.embedder.transform( [text] ).toarray()[0]
                        return result.tolist()

            # SentenceTransformer
            result = self.embedder.encode( [text] )[0]
            if isinstance( result, np.ndarray ) :
                return result.tolist()
            return result
        except Exception as e :
            logger.error( f"Embedding error: {e}" )
            return [0.0] * self._dimension

    def _get_embeddings ( self, texts: List[str] ) -> List[List[float]] :
        """Get embeddings for multiple texts"""
        self._ensure_embedder()

        try :
            # Check if using Ollama service
            if hasattr( self.embedder, 'get_embeddings' ) :
                embeddings = self.embedder.get_embeddings( texts )
                if isinstance( embeddings, np.ndarray ) :
                    return embeddings.tolist()
                return embeddings

            # Check if using TF-IDF
            if hasattr( self.embedder, 'transform' ) :
                # TF-IDF vectorizer — must be fitted before transform
                if not self._tfidf_fitted or not texts:
                    # Fit on provided texts (happens during index_jobs)
                    result = self.embedder.fit_transform( texts ).toarray()
                    self._tfidf_fitted = True
                    self._tfidf_corpus = list(texts)
                    return result.tolist()
                else:
                    try:
                        result = self.embedder.transform( texts ).toarray()
                        return result.tolist()
                    except Exception:
                        # Refit if corpus changed or vectorizer was reset
                        combined = self._tfidf_corpus + list(texts)
                        self.embedder.fit( combined )
                        self._tfidf_fitted = True
                        result = self.embedder.transform( texts ).toarray()
                        return result.tolist()

            # SentenceTransformer
            result = self.embedder.encode( texts )
            if isinstance( result, np.ndarray ) :
                return result.tolist()
            return result
        except Exception as e :
            logger.error( f"Batch embedding error: {e}" )
            return [[0.0] * self._dimension for _ in texts]

    def index_jobs ( self, jobs: List[Dict] ) -> int :
        """Index jobs into vector database with freshness tracking"""
        if not jobs :
            logger.warning( "No jobs to index" )
            return 0

        logger.info( f"Indexing {len( jobs )} jobs..." )

        documents = []
        metadatas = []
        ids = []

        for job in jobs :
            job_id = job.get( "id" )

            if not isinstance( job_id, str ) or not job_id.strip() :
                logger.error( f"Skipping job with invalid id: {job_id}" )
                continue

            title = job.get( "title", "" )
            description = job.get( "description", "" )

            if not isinstance( title, str ) or not title.strip() :
                logger.error( f"Skipping job {job_id}: invalid title" )
                continue

            if not isinstance( description, str ) or not description.strip() :
                logger.warning( f"Job {job_id} has no description, using title only" )
                description = f"We are hiring for {title} position. Apply now!"

            doc_text = f"{title}. {description}" if description else title
            documents.append( doc_text )

            metadatas.append( {
                "title" : str( title ),
                "company" : str( job.get( "company", "Unknown" ) ),
                "location" : str( job.get( "location", "" ) ),
                "apply_link" : str( job.get( "apply_link", "" ) ),
                "employment_type" : str( job.get( "employment_type", "Full-time" ) ),
                "posted_at" : str( job.get( "posted_at", "" ) ),
                "days_old" : str( job.get( "days_old", "0" ) ),
                "fetched_at" : str( job.get( "fetched_at", datetime.now().isoformat() ) ),
                "indexed_at" : datetime.now().isoformat()
            } )

            ids.append( job_id )

        if not documents :
            logger.warning( "No valid jobs left after validation" )
            return 0

        logger.info( "Generating embeddings..." )
        try :
            embeddings = self._get_embeddings( documents )

            logger.info( "Upserting to ChromaDB..." )
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )

            self._count_cache = self.collection.count()
            logger.info( f"Successfully indexed {len( ids )} jobs. Total: {self._count_cache}" )
            return len( ids )

        except Exception as e :
            logger.error( f"Error during indexing: {str( e )}" )
            raise

    def search ( self, query_text: str, top_k: int = 10 ) -> List[Dict] :
        """Semantic search for relevant jobs with freshness boost"""
        logger.info( f"Searching for top {top_k} matches..." )

        total_jobs = self.collection.count()
        if total_jobs == 0 :
            logger.warning( "No jobs in vector store" )
            return []

        try :
            # Generate query embedding
            query_embedding = self._get_embeddings( [query_text] )

            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min( top_k * 2, total_jobs )
            )

            # Parse results
            jobs = []
            if results.get( 'metadatas' ) and len( results['metadatas'] ) > 0 :
                for idx, metadata in enumerate( results['metadatas'][0] ) :
                    base_distance = results['distances'][0][idx] if results.get( 'distances' ) else 0.5

                    days_old = int( metadata.get( "days_old", "7" ) )
                    freshness_boost = 0.1 * max( 0, (30 - min( days_old, 30 )) / 30 )
                    adjusted_distance = max( 0, base_distance - freshness_boost )

                    job = {
                        "id" : results['ids'][0][idx],
                        "title" : metadata.get( "title", "" ),
                        "company" : metadata.get( "company", "" ),
                        "location" : metadata.get( "location", "" ),
                        "description" : results['documents'][0][idx] if results.get( 'documents' ) else "",
                        "apply_link" : metadata.get( "apply_link", "" ),
                        "employment_type" : metadata.get( "employment_type", "Full-time" ),
                        "posted_at" : metadata.get( "posted_at", "" ),
                        "days_old" : int( metadata.get( "days_old", "0" ) ),
                        "fetched_at" : metadata.get( "fetched_at", "" ),
                        "distance" : adjusted_distance,
                        "base_distance" : base_distance
                    }
                    jobs.append( job )

                jobs.sort( key=lambda x : x['distance'] )

            logger.info( f"Found {len( jobs )} matching jobs" )
            return jobs[:top_k]

        except Exception as e :
            logger.error( f"Search error: {e}" )
            return []

    def get_stats ( self ) -> Dict :
        """Get vector store statistics including freshness"""
        # Use cached count; fall back to live count if cache unset
        count_cache = getattr( self, "_count_cache", -1 )

        count = (
            count_cache
            if count_cache >= 0
            else self.collection.count()
        )

        self._count_cache = count

        freshness = "unknown"
        avg_days_old = 0

        if count > 0 :
            try :
                sample_emb = self._get_embeddings( ["software"] )
                sample = self.collection.query(
                    query_embeddings=sample_emb,
                    n_results=min( 10, count )
                )
                if sample.get( 'metadatas' ) :
                    days_old_list = []
                    for meta in sample['metadatas'][0] :
                        days = int( meta.get( "days_old", "7" ) )
                        days_old_list.append( days )

                    if days_old_list :
                        avg_days_old = sum( days_old_list ) / len( days_old_list )
                        if avg_days_old <= 3 :
                            freshness = "very fresh"
                        elif avg_days_old <= 7 :
                            freshness = "fresh"
                        elif avg_days_old <= 14 :
                            freshness = "moderate"
                        else :
                            freshness = "stale"
            except Exception as e :
                logger.error( f"Error checking freshness: {e}" )

        embedder_info = "TF-IDF" if self._use_tfidf else (
            "Ollama" if hasattr( self.embedder, 'available' ) else "SentenceTransformer")

        return {
            "total_jobs" : count,
            "collection_name" : self.collection.name,
            "persist_directory" : settings.CHROMA_PERSIST_DIR,
            "freshness" : freshness,
            "avg_days_old" : round( avg_days_old, 1 ),
            "embedder" : embedder_info
        }

    def clear ( self ) :
        """Clear all jobs from vector store"""
        try :
            self.client.delete_collection( "job_listings" )
            self.collection = self.client.get_or_create_collection( name="job_listings" )
            self._count_cache = 0
            logger.info( "Vector store cleared" )
        except Exception as e :
            logger.error( f"Error clearing vector store: {str( e )}" )


# Singleton instance with graceful failure - no heavy loading at startup
vector_store = None

try :
    vector_store = VectorStore()
    logger.info( "Vector store singleton created (lazy loading enabled)" )
except Exception as e :
    logger.exception( f"VectorStore init failed; starting in degraded mode: {e}" )

    # Remove/refresh the existing chroma sqlite schema if it's stale
    try :
        if hasattr( settings, "CHROMA_PERSIST_DIR" ) :
            persist_dir = Path( settings.CHROMA_PERSIST_DIR )
            sqlite_path = persist_dir / "chroma.sqlite3"
            if sqlite_path.exists() :
                logger.warning( "Deleting stale Chroma sqlite schema at %s", sqlite_path )
                sqlite_path.unlink()
    except Exception as cleanup_exc :
        logger.warning( f"Chroma schema cleanup failed: {cleanup_exc}" )