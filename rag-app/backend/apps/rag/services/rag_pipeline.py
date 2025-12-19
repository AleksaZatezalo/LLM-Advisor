"""
RAG Pipeline.

Orchestrates the full RAG workflow:
1. Document ingestion (PDF → chunks → embeddings → vector store)
2. Query processing (question → embedding → search → context → LLM → answer)
"""
from dataclasses import dataclass
from .pdf_processor import PDFProcessor
from .embedding_service import get_embedding_service
from .vector_store import VectorStore, SearchResult
from .llm_service import LLMService


@dataclass
class RAGResponse:
    """Response from a RAG query."""
    answer: str
    sources: list[dict]


class RAGPipeline:
    """
    Orchestrates the RAG workflow.
    
    Provides high-level methods for document ingestion and question answering.
    """
    
    SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.

Instructions:
- Answer the question using ONLY the information from the context below
- If the context doesn't contain enough information, say so clearly
- Cite specific sections when relevant
- Be concise and direct

Context:
{context}
"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.embedding_service = get_embedding_service()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
    
    def ingest_document(self, file_path: str, document_id: str) -> int:
        """
        Ingest a PDF document into the RAG system.
        
        Args:
            file_path: Path to the PDF file
            document_id: Unique identifier for the document
        
        Returns:
            Number of chunks created
        """
        # Extract and chunk the PDF
        chunks = self.pdf_processor.process_document(file_path, document_id)
        
        if not chunks:
            return 0
        
        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Prepare data for vector store
        ids = [f"{document_id}_{chunk.chunk_index}" for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Store in vector database
        self.vector_store.add_documents(
            ids=ids,
            embeddings=embeddings,
            contents=texts,
            metadatas=metadatas,
        )
        
        return len(chunks)
    
    def query(
        self,
        question: str,
        document_ids: list[str] = None,
        top_k: int = 5,
    ) -> RAGResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: The user's question
            document_ids: Optional filter to specific documents
            top_k: Number of context chunks to retrieve
        
        Returns:
            RAGResponse with answer and source references
        """
        # Embed the question
        query_embedding = self.embedding_service.embed_text(question)
        
        # Search for relevant chunks
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
        
        # Build context from search results
        context = self._build_context(results)
        
        # Generate answer using LLM
        system_prompt = self.SYSTEM_PROMPT.format(context=context)
        
        llm_response = self.llm_service.generate(
            prompt=question,
            system=system_prompt,
        )
        
        # Format sources
        sources = [
            {
                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "document_id": r.document_id,
                "page_number": r.page_number,
                "relevance_score": round(r.score, 3),
            }
            for r in results
        ]
        
        return RAGResponse(
            answer=llm_response.content,
            sources=sources,
        )
    
    def _build_context(self, results: list[SearchResult]) -> str:
        """Build context string from search results."""
        if not results:
            return "No relevant context found."
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] (Page {result.page_number}, Relevance: {result.score:.2f})\n"
                f"{result.content}"
            )
        
        return "\n\n".join(context_parts)
    
    def delete_document(self, document_id: str) -> None:
        """Remove a document from the RAG system."""
        self.vector_store.delete_document(document_id)
