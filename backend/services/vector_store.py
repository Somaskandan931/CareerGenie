import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        """Initialize ChromaDB and embedding model"""
        # Ensure directory exists
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at: {persist_dir}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="job_listings",
            metadata={"description": "Job listings for RAG matching"}
        )

        # Load embedding model
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)

        logger.info(f"Vector store initialized. Current jobs: {self.collection.count()}")

    def index_jobs(self, jobs: List[Dict]) -> int:
        """Index jobs into vector database"""
        if not jobs:
            logger.warning("No jobs to index")
            return 0

        logger.info(f"Indexing {len(jobs)} jobs...")

        documents = []
        metadatas = []
        ids = []

        for job in jobs:
            job_id = job.get("id")

            # Validate job_id is string
            if not isinstance(job_id, str) or not job_id.strip():
                logger.error(f"Skipping job with invalid id: {job_id}")
                continue

            title = job.get("title", "")
            description = job.get("description", "")

            if not isinstance(title, str) or not title.strip():
                logger.error(f"Skipping job {job_id}: invalid title")
                continue

            if not isinstance(description, str) or not description.strip():
                logger.warning(f"Job {job_id} has no description, using title only")
                description = ""

            # Combine title and description for embedding
            doc_text = f"{title}. {description}" if description else title
            documents.append(doc_text)

            metadatas.append({
                "title": str(title),
                "company": str(job.get("company", "Unknown")),
                "location": str(job.get("location", "")),
                "apply_link": str(job.get("apply_link", "")),
                "employment_type": str(job.get("employment_type", "Full-time")),
                "posted_at": str(job.get("posted_at", ""))
            })

            ids.append(job_id)

        if not documents:
            logger.warning("No valid jobs left after validation")
            return 0

        logger.info("Generating embeddings...")
        try:
            embeddings = self.embedder.encode(
                documents,
                show_progress_bar=False,
                batch_size=32
            ).tolist()

            logger.info("Upserting to ChromaDB...")
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )

            logger.info(f"Successfully indexed {len(ids)} jobs. Total: {self.collection.count()}")
            return len(ids)

        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            raise

    def search(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """Semantic search for relevant jobs"""
        logger.info(f"Searching for top {top_k} matches...")

        total_jobs = self.collection.count()
        if total_jobs == 0:
            logger.warning("No jobs in vector store")
            return []

        # Generate query embedding
        query_embedding = self.embedder.encode([query_text]).tolist()

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, total_jobs)
        )

        # Parse results
        jobs = []
        if results.get('metadatas') and len(results['metadatas']) > 0:
            for idx, metadata in enumerate(results['metadatas'][0]):
                job = {
                    "id": results['ids'][0][idx],
                    "title": metadata.get("title", ""),
                    "company": metadata.get("company", ""),
                    "location": metadata.get("location", ""),
                    "description": results['documents'][0][idx] if results.get('documents') else "",
                    "apply_link": metadata.get("apply_link", ""),
                    "employment_type": metadata.get("employment_type", "Full-time"),
                    "distance": results['distances'][0][idx] if results.get('distances') else 0.5
                }
                jobs.append(job)

        logger.info(f"Found {len(jobs)} matching jobs")
        return jobs

    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            "total_jobs": self.collection.count(),
            "collection_name": self.collection.name,
            "persist_directory": settings.CHROMA_PERSIST_DIR
        }

    def clear(self):
        """Clear all jobs from vector store"""
        try:
            self.client.delete_collection("job_listings")
            self.collection = self.client.get_or_create_collection(name="job_listings")
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")


# Singleton instance
vector_store = VectorStore()