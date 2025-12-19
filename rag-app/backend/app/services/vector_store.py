import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import hashlib
import os

from app.config import get_settings


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        self._embedder = SentenceTransformer(settings.embedding_model)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

    def add_pdf(self, filepath: str, filename: str) -> tuple[str, int]:
        """Extract text from PDF, chunk it, embed it, store it. Returns (doc_id, chunk_count)."""
        text = self._extract_pdf_text(filepath)
        chunks = self._splitter.split_text(text)
        
        doc_id = hashlib.md5(filename.encode()).hexdigest()[:12]
        
        embeddings = self._embedder.encode(chunks).tolist()
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
        
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return doc_id, len(chunks)

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """Query the vector store and return relevant chunks with metadata."""
        embedding = self._embedder.encode([question]).tolist()
        
        results = self._collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "content": doc,
                "source": meta["source"],
                "score": 1 - dist  # Convert distance to similarity
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]

    def list_documents(self) -> list[dict]:
        """List all unique documents in the store."""
        all_meta = self._collection.get(include=["metadatas"])
        
        docs = {}
        for meta in all_meta["metadatas"]:
            doc_id = meta["doc_id"]
            if doc_id not in docs:
                docs[doc_id] = {"id": doc_id, "filename": meta["source"], "chunk_count": 0}
            docs[doc_id]["chunk_count"] += 1
        
        return list(docs.values())

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        results = self._collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            return True
        return False

    def _extract_pdf_text(self, filepath: str) -> str:
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


# Singleton instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
