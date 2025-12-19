# RAG Document Assistant

A fully offline RAG (Retrieval-Augmented Generation) system with a Django backend and React frontend. Upload PDFs and ask questions - the system retrieves relevant context and generates answers using a local LLM.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   React     │   Django    │   Ollama    │    ChromaDB       │
│  Frontend   │   Backend   │    LLM      │   Vector Store    │
│   :3000     │   :8000     │   :11434    │    :8001          │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

**Components:**
- **Frontend**: React with Tailwind CSS
- **Backend**: Django REST Framework
- **LLM**: Ollama (runs locally, fully offline)
- **Vector Store**: ChromaDB (similarity search)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)

## Quick Start

```bash
# 1. Start all services
docker-compose up -d --build

# 2. Pull an LLM model (first time only, ~4GB download)
docker exec -it rag-ollama ollama pull llama3.2

# 3. Access the application
open http://localhost:3000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | System health check |
| `/api/documents/` | GET | List all documents |
| `/api/documents/` | POST | Upload a PDF |
| `/api/documents/<id>/` | DELETE | Delete a document |
| `/api/query/` | POST | Ask a question |
| `/api/sessions/` | GET | List chat sessions |
| `/api/models/pull/` | POST | Pull an Ollama model |

## Usage

### Upload Documents
1. Click the "Documents" tab
2. Drag and drop PDF files or click to browse
3. Wait for processing to complete (status shows "completed")

### Ask Questions
1. Click the "Chat" tab  
2. Type your question and press Enter
3. View the answer with source citations
4. Click "X sources" to expand and see the relevant passages

## Configuration

Environment variables (in `docker-compose.yml`):

```yaml
# LLM Settings
OLLAMA_HOST: http://ollama:11434
OLLAMA_MODEL: llama3.2  # Change to use different model

# Vector Store
CHROMA_HOST: chromadb
CHROMA_PORT: 8000

# Django
DEBUG: 1  # Set to 0 in production
```

### Changing the LLM Model

```bash
# Pull a different model
docker exec -it rag-ollama ollama pull mistral

# Update OLLAMA_MODEL in docker-compose.yml
# Restart backend
docker-compose restart backend
```

Available models: `llama3.2`, `mistral`, `phi3`, `gemma2`, etc.

## Project Structure

```
rag-app/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/                 # Django settings
│   │   ├── settings.py
│   │   └── urls.py
│   └── apps/
│       └── rag/               # RAG application
│           ├── models.py      # Document, ChatSession, ChatMessage
│           ├── views.py       # API endpoints
│           ├── serializers.py # DRF serializers
│           ├── urls.py        # URL routing
│           └── services/      # Business logic
│               ├── pdf_processor.py      # PDF extraction & chunking
│               ├── embedding_service.py  # sentence-transformers
│               ├── vector_store.py       # ChromaDB interface
│               ├── llm_service.py        # Ollama client
│               └── rag_pipeline.py       # Orchestration
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── public/
    └── src/
        ├── App.js
        ├── services/
        │   └── api.js         # API client
        └── components/
            ├── DocumentPanel.js
            ├── ChatPanel.js
            └── StatusBar.js
```

## Development

### Backend Only
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Only
```bash
cd frontend
npm install
npm start
```

## Troubleshooting

**LLM not responding:**
```bash
# Check if Ollama is running
docker logs rag-ollama

# Ensure model is pulled
docker exec -it rag-ollama ollama list
```

**ChromaDB connection error:**
```bash
# Check ChromaDB status
docker logs rag-chromadb
```

**Slow first query:**
- The embedding model downloads on first use (~90MB)
- LLM model loads into memory on first query

## License

MIT
