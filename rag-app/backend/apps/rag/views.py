"""
API Views for RAG application.

Provides REST endpoints for:
- Document upload and management
- RAG queries
- Chat sessions
- System health
"""
import os
import uuid
from pathlib import Path

from django.conf import settings as django_settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from .models import Document, ChatSession, ChatMessage
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    ChatSessionSerializer,
    QuerySerializer,
    QueryResponseSerializer,
)
from .services import RAGPipeline, LLMService


class HealthView(APIView):
    """System health check endpoint."""
    
    def get(self, request):
        llm = LLMService()
        
        return Response({
            "status": "healthy",
            "ollama_available": llm.is_available(),
            "available_models": llm.list_models(),
        })


class DocumentListView(APIView):
    """List and upload documents."""
    
    parser_classes = [MultiPartParser]
    
    def get(self, request):
        """List all documents."""
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Upload a new document."""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        
        # Ensure upload directory exists
        upload_dir = Path(django_settings.MEDIA_ROOT) / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / filename
        
        # Save file
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Create document record
        document = Document.objects.create(
            filename=filename,
            original_filename=uploaded_file.name,
            file_path=str(file_path),
            file_size=uploaded_file.size,
            status='processing',
        )
        
        # Process document through RAG pipeline
        try:
            pipeline = RAGPipeline()
            chunk_count = pipeline.ingest_document(
                file_path=str(file_path),
                document_id=str(document.id),
            )
            
            # Update document with processing results
            from .services.pdf_processor import PDFProcessor
            processor = PDFProcessor()
            _, page_count = processor.extract_text(str(file_path))
            
            document.page_count = page_count
            document.chunk_count = chunk_count
            document.status = 'completed'
            document.save()
            
        except Exception as e:
            document.status = 'failed'
            document.error_message = str(e)
            document.save()
            
            return Response(
                {"error": f"Processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    """Retrieve and delete individual documents."""
    
    def get(self, request, document_id):
        """Get document details."""
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        return Response(DocumentSerializer(document).data)
    
    def delete(self, request, document_id):
        """Delete a document."""
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Remove from vector store
        try:
            pipeline = RAGPipeline()
            pipeline.delete_document(str(document.id))
        except Exception:
            pass  # Continue even if vector store deletion fails
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete database record
        document.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class QueryView(APIView):
    """RAG query endpoint."""
    
    def post(self, request):
        """Ask a question using RAG."""
        serializer = QuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        session_id = serializer.validated_data.get('session_id')
        
        # Get or create chat session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create()
        else:
            session = ChatSession.objects.create()
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=question,
        )
        
        # Run RAG query
        try:
            pipeline = RAGPipeline()
            result = pipeline.query(question=question)
            
            # Save assistant response
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=result.answer,
                sources=result.sources,
            )
            
            response_data = {
                "answer": result.answer,
                "sources": result.sources,
                "session_id": str(session.id),
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {"error": f"Query failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatSessionListView(APIView):
    """List chat sessions."""
    
    def get(self, request):
        """List all chat sessions."""
        sessions = ChatSession.objects.all()[:20]  # Last 20 sessions
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class ChatSessionDetailView(APIView):
    """Get chat session with messages."""
    
    def get(self, request, session_id):
        """Get session with full message history."""
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        return Response(ChatSessionSerializer(session).data)
    
    def delete(self, request, session_id):
        """Delete a chat session."""
        try:
            session = ChatSession.objects.get(id=session_id)
            session.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ModelPullView(APIView):
    """Pull an Ollama model."""
    
    def post(self, request):
        """Pull a model from Ollama registry."""
        model_name = request.data.get('model', django_settings.OLLAMA_MODEL)
        
        llm = LLMService()
        
        if not llm.is_available():
            return Response(
                {"error": "Ollama is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        
        success = llm.pull_model(model_name)
        
        if success:
            return Response({"status": "success", "model": model_name})
        else:
            return Response(
                {"error": f"Failed to pull model: {model_name}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
