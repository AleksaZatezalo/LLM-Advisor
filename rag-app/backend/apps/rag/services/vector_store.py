"""
Vector Store Service.

Manages document embeddings in ChromaDB for similarity search.
"""
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from django.conf import settings as django_settings


@dataclass
class SearchResult:
    """Represents a search result from the vector store."""
    content: str
    document_id: str
    page_number: int
    chunk_index: int
    score: float  # similarity score (higher = more similar)


class VectorStore:
    """
    Interface to ChromaDB for storing and querying document embeddings.
    
    Uses a single collection for all documents, with metadata filtering
    to support document-specific queries.
    """
    
    COLLECTION_NAME = "documents"
    
    def __init__(self):
        self._client = None
        self._collection = None
    
    @property
    def client(self) -> chromadb.HttpClient:
        """Lazy-load ChromaDB client."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=django_settings.CHROMA_HOST,
                port=django_settings.CHROMA_PORT,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client
    
    @property
    def collection(self):
        """Get or create the documents collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection
    
    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        contents: list[str],
        metadatas: list[dict],
    ) -> None:
        """
        Add document chunks to the vector store.
        
        Args:
            ids: Unique identifiers for each chunk
            embeddings: Pre-computed embeddings
            contents: Text content of each chunk
            metadatas: Metadata dicts (page_number, document_id, etc.)
        """
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = None,
        document_ids: list[str] = None,
    ) -> list[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: The query vector
            top_k: Number of results to return
            document_ids: Optional filter to specific documents
        
        Returns:
            List of SearchResult objects, sorted by similarity
        """
        top_k = top_k or django_settings.TOP_K_RESULTS
        
        # Build where filter if document_ids specified
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        search_results = []
        
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # ChromaDB returns distances; convert to similarity score
                # For cosine distance: similarity = 1 - distance
                distance = results['distances'][0][i]
                similarity = 1 - distance
                
                metadata = results['metadatas'][0][i]
                
                search_results.append(SearchResult(
                    content=results['documents'][0][i],
                    document_id=metadata.get('document_id', ''),
                    page_number=metadata.get('page_number', 0),
                    chunk_index=metadata.get('chunk_index', 0),
                    score=similarity,
                ))
        
        return search_results
    
    def delete_document(self, document_id: str) -> None:
        """Remove all chunks for a specific document."""
        self.collection.delete(
            where={"document_id": document_id}
        )
    
    def get_stats(self) -> dict:
        """Get collection statistics."""
        return {
            "total_chunks": self.collection.count(),
        }
