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

from backend.config import settings

logger = logging.getLogger( __name__ )


class VectorStore :
    def __init__ ( self ) :
        """Initialize ChromaDB and embedding model (Ollama first, fallback to SentenceTransformer)"""
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

        # Load embedding model - try Ollama first
        self.embedder = self._init_embedder()
        self._dimension = 384  # all-minilm dimension

        logger.info( f"Vector store initialized. Current jobs: {self.collection.count()}" )

    def _init_embedder ( self ) :
        """Initialize embedder - Ollama first, then SentenceTransformer fallback"""
        # Try Ollama first
        try :
            from backend.services.ollama_service import get_ollama_service
            ollama_svc = get_ollama_service()
            if ollama_svc.available :
                logger.info( f"Using Ollama for embeddings (model: {ollama_svc.embedding_model})" )
                return ollama_svc
        except Exception as e :
            logger.warning( f"Ollama not available: {e}" )

        # Fallback to SentenceTransformer
        try :
            from sentence_transformers import SentenceTransformer
            logger.info( f"Falling back to SentenceTransformer model: {settings.EMBEDDING_MODEL}" )
            return SentenceTransformer( settings.EMBEDDING_MODEL )
        except Exception as e :
            logger.error( f"Failed to load any embedder: {e}" )
            raise RuntimeError( "No embedding model available. Install Ollama or sentence-transformers" )

    def _get_embedding ( self, text: str ) -> List[float] :
        """Get embedding for a single text"""
        try :
            # Check if using Ollama service
            if hasattr( self.embedder, 'get_embedding' ) :
                embedding = self.embedder.get_embedding( text )
                if isinstance( embedding, np.ndarray ) :
                    return embedding.tolist()
                return embedding
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
        try :
            # Check if using Ollama service
            if hasattr( self.embedder, 'get_embeddings' ) :
                embeddings = self.embedder.get_embeddings( texts )
                if isinstance( embeddings, np.ndarray ) :
                    return embeddings.tolist()
                return embeddings
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

            logger.info( f"Successfully indexed {len( ids )} jobs. Total: {self.collection.count()}" )
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
        count = self.collection.count()

        freshness = "unknown"
        avg_days_old = 0

        if count > 0 :
            try :
                sample = self.collection.query(
                    query_texts=["software"],
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

        embedder_info = "Ollama" if hasattr( self.embedder, 'available' ) else "SentenceTransformer"

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
            logger.info( "Vector store cleared" )
        except Exception as e :
            logger.error( f"Error clearing vector store: {str( e )}" )


# Singleton instance
vector_store = VectorStore()