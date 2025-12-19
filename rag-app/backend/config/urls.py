"""URL configuration for RAG application."""
from django.urls import path, include

urlpatterns = [
    path('api/', include('apps.rag.urls')),
]
