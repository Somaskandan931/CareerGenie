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
    Manages job embeddings and similarity search using ChromaDB
    """

    def __init__ ( self, persist_directory: str = "./chroma_db" ) :
        """Initialize vector store with persistent storage"""
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.Client( Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ) )

        # Initialize embedding model (all-MiniLM-L6-v2 is fast and good)
        self.embedder = SentenceTransformer( 'sentence-transformers/all-MiniLM-L6-v2' )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description" : "Job posting embeddings for RAG matching"}
        )

        logger.info( f"Vector store initialized with {self.collection.count()} jobs" )

    def _create_job_text ( self, job: Dict[str, Any] ) -> str :
        """
        Convert job dict to searchable text representation
        This is what gets embedded for semantic search
        """
        parts = [
            f"Job Title: {job['title']}",
            f"Company: {job['company']}",
            f"Location: {job['location']}",
            f"Required Skills: {', '.join( job['skills_required'] )}",
            f"Preferred Skills: {', '.join( job.get( 'skills_preferred', [] ) )}",
            f"Experience: {job['experience_required']}",
            f"Description: {job['description']}",
            f"Responsibilities: {' '.join( job.get( 'responsibilities', [] ) )}"
        ]
        return "\n".join( parts )

    def load_jobs_from_file ( self, json_path: str ) -> int :
        """
        Load jobs from JSON file and add to vector store

        Returns:
            Number of jobs added
        """
        path = Path( json_path )
        if not path.exists() :
            logger.error( f"Jobs file not found: {json_path}" )
            return 0

        with open( path, 'r' ) as f :
            jobs = json.load( f )

        return self.add_jobs( jobs )

    def add_jobs ( self, jobs: List[Dict[str, Any]] ) -> int :
        """
        Add jobs to vector store

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of jobs added
        """
        if not jobs :
            return 0

        # Prepare data for ChromaDB
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

        # Generate embeddings
        embeddings = self.embedder.encode( documents ).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.info( f"Added {len( jobs )} jobs to vector store" )
        return len( jobs )

    def search_jobs ( self, resume_text: str, top_k: int = 10 ) -> List[Dict[str, Any]] :
        """
        Search for jobs matching resume using semantic similarity

        Args:
            resume_text: Plain text from parsed resume
            top_k: Number of top matches to return

        Returns:
            List of matched jobs with similarity scores
        """
        # Generate resume embedding
        resume_embedding = self.embedder.encode( resume_text ).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[resume_embedding],
            n_results=top_k,
            include=['metadatas', 'documents', 'distances']
        )

        # Format results
        matched_jobs = []
        for i in range( len( results['ids'][0] ) ) :
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            # Convert cosine distance to similarity score (0-100)
            # ChromaDB returns L2 distance, convert to similarity
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
        """Clear all jobs from vector store"""
        self.client.delete_collection( "job_postings" )
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description" : "Job posting embeddings for RAG matching"}
        )
        logger.info( "Vector store cleared" )

    def get_stats ( self ) -> Dict[str, Any] :
        """Get vector store statistics"""
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