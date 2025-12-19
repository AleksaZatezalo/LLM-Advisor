import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import get_settings
from app.models import QueryRequest, QueryResponse, DocumentInfo, UploadResponse
from app.services import get_vector_store, get_rag_service, get_llm_service


router = APIRouter()


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF and process it into the vector store."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    settings = get_settings()
    os.makedirs(settings.upload_path, exist_ok=True)
    
    filepath = os.path.join(settings.upload_path, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    try:
        vector_store = get_vector_store()
        doc_id, chunk_count = vector_store.add_pdf(filepath, file.filename)
        return UploadResponse(
            message="Document processed successfully",
            document_id=doc_id,
            chunks_created=chunk_count
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to process document: {str(e)}")


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    vector_store = get_vector_store()
    return vector_store.list_documents()


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the vector store."""
    vector_store = get_vector_store()
    if vector_store.delete_document(doc_id):
        return {"message": "Document deleted"}
    raise HTTPException(404, "Document not found")


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system with a question."""
    rag = get_rag_service()
    result = await rag.query(request.question, top_k=request.top_k)
    return QueryResponse(**result)


@router.get("/health")
async def health_check():
    """Check system health including Ollama connection."""
    llm = get_llm_service()
    ollama_healthy = await llm.check_health()
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": "connected" if ollama_healthy else "disconnected"
    }
