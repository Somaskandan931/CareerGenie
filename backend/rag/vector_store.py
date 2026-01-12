import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger( __name__ )


class JobVectorStore :
    """
    Optimized vector store with faster embeddings and batch processing
    """

    def __init__ ( self, persist_directory: str = "./chroma_db" ) :
        """Initialize vector store"""
        self.persist_directory = persist_directory

        # Initialize ChromaDB
        self.client = chromadb.Client( Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ) )

        # Use faster, smaller embedding model
        # all-MiniLM-L6-v2: 384 dimensions, very fast
        self.embedder = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2',
            device='cpu'  # Explicit CPU for stability
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description" : "Job posting embeddings"}
        )

        logger.info( f"Vector store ready: {self.collection.count()} jobs" )

    def _create_job_text ( self, job: Dict[str, Any] ) -> str :
        """
        Optimized job text representation - shorter for faster embeddings
        """
        # Only include essential fields
        parts = [
            f"Title: {job['title']}",
            f"Company: {job['company']}",
            f"Skills: {', '.join( job['skills_required'][:5] )}",  # Max 5 skills
            f"Experience: {job['experience_required']}",
            f"Description: {job['description'][:300]}"  # Truncate description
        ]
        return " | ".join( parts )

    def add_jobs ( self, jobs: List[Dict[str, Any]] ) -> int :
        """
        Optimized job addition with batch embeddings
        """
        if not jobs :
            return 0

        # Prepare data
        ids = [job['job_id'] for job in jobs]
        documents = [self._create_job_text( job ) for job in jobs]

        metadatas = [
            {
                "title" : job['title'],
                "company" : job['company'],
                "location" : job['location'],
                "skills_required" : json.dumps( job['skills_required'] ),
                "skills_preferred" : json.dumps( job.get( 'skills_preferred', [] ) ),
                "experience_required" : job['experience_required'],
                "salary_range" : job.get( 'salary_range', 'Not specified' ),
                "apply_link" : job['apply_link'],
                "employment_type" : job.get( 'employment_type', 'Full-time' )
            }
            for job in jobs
        ]

        # Batch encode - much faster than one-by-one
        logger.info( f"Encoding {len( jobs )} jobs..." )
        embeddings = self.embedder.encode(
            documents,
            batch_size=32,  # Process in batches
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.info( f"✅ Added {len( jobs )} jobs" )
        return len( jobs )

    def search_jobs ( self, resume_text: str, top_k: int = 10 ) -> List[Dict[str, Any]] :
        """
        Optimized semantic search
        """
        # Truncate resume text for faster embedding
        resume_text_truncated = resume_text[:1000]

        # Generate resume embedding
        resume_embedding = self.embedder.encode(
            resume_text_truncated,
            convert_to_numpy=True
        ).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[resume_embedding],
            n_results=min( top_k, 20 ),  # Cap at 20 for speed
            include=['metadatas', 'documents', 'distances']
        )

        # Format results
        matched_jobs = []
        for i in range( len( results['ids'][0] ) ) :
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            # Convert distance to similarity (0-100)
            similarity_score = max( 0, (1 - distance) * 100 )

            matched_jobs.append( {
                "job_id" : results['ids'][0][i],
                "title" : metadata['title'],
                "company" : metadata['company'],
                "location" : metadata['location'],
                "skills_required" : json.loads( metadata['skills_required'] ),
                "skills_preferred" : json.loads( metadata['skills_preferred'] ),
                "experience_required" : metadata['experience_required'],
                "salary_range" : metadata['salary_range'],
                "apply_link" : metadata['apply_link'],
                "employment_type" : metadata['employment_type'],
                "similarity_score" : round( similarity_score, 2 ),
                "job_description" : results['documents'][0][i]
            } )

        return matched_jobs

    def clear_all ( self ) :
        """Clear all jobs"""
        self.client.delete_collection( "job_postings" )
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description" : "Job posting embeddings"}
        )
        logger.info( "Vector store cleared" )

    def get_stats ( self ) -> Dict[str, Any] :
        """Get statistics"""
        return {
            "total_jobs" : self.collection.count(),
            "model" : "all-MiniLM-L6-v2",
            "persist_directory" : self.persist_directory
        }


# Global instance
_vector_store = None


def get_vector_store () -> JobVectorStore :
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None :
        _vector_store = JobVectorStore()
    return _vector_store