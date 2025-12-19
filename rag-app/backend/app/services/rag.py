from app.services.vector_store import get_vector_store
from app.services.llm import get_llm_service


RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on the provided context.
Use ONLY the information from the context below to answer the question.
If the context doesn't contain enough information to answer, say so clearly.

Context:
{context}

Question: {question}

Answer:"""


class RAGService:
    def __init__(self):
        self._vector_store = get_vector_store()
        self._llm = get_llm_service()

    async def query(self, question: str, top_k: int = 3) -> dict:
        """Retrieve relevant chunks and generate an answer."""
        # Retrieve
        chunks = self._vector_store.query(question, top_k=top_k)
        
        if not chunks:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "sources": []
            }
        
        # Build context
        context = "\n\n---\n\n".join(
            f"[Source: {c['source']}]\n{c['content']}" for c in chunks
        )
        
        # Generate
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
        answer = await self._llm.generate(prompt)
        
        return {
            "answer": answer,
            "sources": [{"source": c["source"], "score": c["score"]} for c in chunks]
        }


# Singleton
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
