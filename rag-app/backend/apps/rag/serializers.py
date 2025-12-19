"""
Serializers for RAG API endpoints.
"""
from rest_framework import serializers
from .models import Document, ChatSession, ChatMessage


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'original_filename', 'file_size',
            'page_count', 'chunk_count', 'status', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload requests."""
    
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are supported.")
        
        # 50MB limit
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB.")
        
        return value


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'sources', 'created_at']
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions with messages."""
    
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'created_at', 'messages']
        read_only_fields = fields


class QuerySerializer(serializers.Serializer):
    """Serializer for RAG query requests."""
    
    question = serializers.CharField(max_length=2000)
    session_id = serializers.UUIDField(required=False, allow_null=True)


class QueryResponseSerializer(serializers.Serializer):
    """Serializer for RAG query responses."""
    
    answer = serializers.CharField()
    sources = serializers.ListField(child=serializers.DictField())
    session_id = serializers.UUIDField()
