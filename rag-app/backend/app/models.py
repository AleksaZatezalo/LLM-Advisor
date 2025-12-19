from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int


class UploadResponse(BaseModel):
    message: str
    document_id: str
    chunks_created: int
