"""URL configuration for RAG API."""
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.HealthView.as_view(), name='health'),
    
    # Documents
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/<uuid:document_id>/', views.DocumentDetailView.as_view(), name='document-detail'),
    
    # RAG Query
    path('query/', views.QueryView.as_view(), name='query'),
    
    # Chat sessions
    path('sessions/', views.ChatSessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/', views.ChatSessionDetailView.as_view(), name='session-detail'),
    
    # Model management
    path('models/pull/', views.ModelPullView.as_view(), name='model-pull'),
]
