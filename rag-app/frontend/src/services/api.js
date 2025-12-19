/**
 * API Service Layer
 * 
 * Centralized API client for all backend communication.
 */
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Health
// ============================================================================

export async function checkHealth() {
  const response = await api.get('/health/');
  return response.data;
}

// ============================================================================
// Documents
// ============================================================================

export async function listDocuments() {
  const response = await api.get('/documents/');
  return response.data;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/documents/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function getDocument(documentId) {
  const response = await api.get(`/documents/${documentId}/`);
  return response.data;
}

export async function deleteDocument(documentId) {
  await api.delete(`/documents/${documentId}/`);
}

// ============================================================================
// RAG Query
// ============================================================================

export async function askQuestion(question, sessionId = null) {
  const payload = { question };
  if (sessionId) {
    payload.session_id = sessionId;
  }
  
  const response = await api.post('/query/', payload);
  return response.data;
}

// ============================================================================
// Chat Sessions
// ============================================================================

export async function listSessions() {
  const response = await api.get('/sessions/');
  return response.data;
}

export async function getSession(sessionId) {
  const response = await api.get(`/sessions/${sessionId}/`);
  return response.data;
}

export async function deleteSession(sessionId) {
  await api.delete(`/sessions/${sessionId}/`);
}

// ============================================================================
// Models
// ============================================================================

export async function pullModel(modelName) {
  const response = await api.post('/models/pull/', { model: modelName });
  return response.data;
}

export default api;
