"""
PDF Processing Service.

Handles PDF text extraction and chunking for RAG pipeline.
"""
from dataclasses import dataclass
from typing import Iterator
import fitz  # PyMuPDF
from django.conf import settings


@dataclass
class TextChunk:
    """Represents a chunk of text from a PDF."""
    content: str
    page_number: int
    chunk_index: int
    document_id: str
    
    @property
    def metadata(self) -> dict:
        return {
            'page_number': self.page_number,
            'chunk_index': self.chunk_index,
            'document_id': self.document_id,
        }


class PDFProcessor:
    """
    Extracts and chunks text from PDF documents.
    
    Uses PyMuPDF for extraction and implements sliding window chunking
    to maintain context across chunk boundaries.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def extract_text(self, file_path: str) -> tuple[str, int]:
        """
        Extract all text from a PDF file.
        
        Returns:
            Tuple of (full_text, page_count)
        """
        doc = fitz.open(file_path)
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        page_count = len(doc)
        doc.close()
        
        return '\n'.join(text_parts), page_count
    
    def extract_pages(self, file_path: str) -> list[tuple[int, str]]:
        """
        Extract text page by page.
        
        Returns:
            List of (page_number, page_text) tuples
        """
        doc = fitz.open(file_path)
        pages = []
        
        for i, page in enumerate(doc):
            pages.append((i + 1, page.get_text()))
        
        doc.close()
        return pages
    
    def chunk_text(self, text: str, document_id: str, page_number: int = 1) -> Iterator[TextChunk]:
        """
        Split text into overlapping chunks.
        
        Uses a sliding window approach to maintain context.
        """
        if not text.strip():
            return
        
        words = text.split()
        chunk_index = 0
        start = 0
        
        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_content = ' '.join(chunk_words)
            
            if chunk_content.strip():
                yield TextChunk(
                    content=chunk_content,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    document_id=document_id,
                )
                chunk_index += 1
            
            # Move window forward, accounting for overlap
            start = end - self.chunk_overlap
            if start >= len(words):
                break
    
    def process_document(self, file_path: str, document_id: str) -> list[TextChunk]:
        """
        Full pipeline: extract and chunk a PDF document.
        
        Processes page by page to maintain accurate page numbers in metadata.
        """
        pages = self.extract_pages(file_path)
        all_chunks = []
        
        for page_number, page_text in pages:
            chunks = list(self.chunk_text(page_text, document_id, page_number))
            all_chunks.extend(chunks)
        
        # Re-index chunks sequentially
        for i, chunk in enumerate(all_chunks):
            chunk.chunk_index = i
        
        return all_chunks
