# AI Business Meeting Assistant - Backend

The backend for the **AI Business Meeting Assistant**, built using **FastAPI**, **MongoDB (PyMongo)**, **local OpenAI Whisper** for speech-to-text audio transcription, **Document/Text Ingestion** (PDF, DOCX, TXT, pasted notes), **AI-powered Meeting Analysis** powered by **Groq Cloud (Llama 3.3)**, **Action-Item Extraction & Persistent Task Management**, and **LangGraph End-to-End Workflow Pipeline Orchestration**.

---

## 1. Prerequisites

- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **MongoDB** (Local Community Server running on `mongodb://localhost:27017` or a MongoDB Atlas connection string)
- **FFmpeg** (Required by OpenAI Whisper for decoding recorded audio files)
- **Groq API Key** (Optional for unit tests; required for live AI meeting intelligence and task extraction from [Groq Console](https://console.groq.com/))

### Installing FFmpeg on Windows

Using [Winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/) or [Chocolatey](https://chocolatey.org/):

```powershell
# Using Winget
winget install Gyan.FFmpeg

# Or using Chocolatey
choco install ffmpeg
```

Verify the installation:
```powershell
ffmpeg -version
```

---

## 2. Project Structure

```text
backend/
├── app/
│   ├── __init__.py                  # Application package
│   ├── main.py                      # FastAPI app, lifespan, CORS, and health endpoints
│   ├── config.py                    # Pydantic Settings & environment variables
│   ├── database.py                  # PyMongo connection management and index creation
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── transcriptions.py        # Audio upload, status, list, edit, delete endpoints
│   │   ├── documents.py             # Document upload (PDF, DOCX, TXT), pasted text endpoints
│   │   ├── analysis.py              # AI meeting analysis generation, retrieval, deletion
│   │   ├── tasks.py                 # Action item extraction, CRUD, follow-up plan, exports
│   │   └── workflows.py             # LangGraph workflow start, status, result, list, retry
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── meeting_workflow.py      # LangGraph StateGraph pipeline, nodes, state TypedDict
│   │   └── workflow_engine.py       # Workflow execution engine and MongoDB state tracking
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whisper_service.py       # OpenAI Whisper model loader & inference engine
│   │   ├── transcription_worker.py  # Concurrency-controlled background audio worker
│   │   ├── document_service.py      # Document extraction & text normalization service
│   │   ├── llm_service.py           # LLM provider abstraction & Groq Cloud client
│   │   ├── meeting_analysis_service.py # Structured extraction, chunking, and synthesis
│   │   ├── task_service.py          # Action-item extraction & follow-up planning service
│   │   └── export_service.py        # Multi-format export service (JSON, CSV, Markdown)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── transcription_repo.py    # MongoDB CRUD repository for transcriptions
│   │   ├── document_repo.py         # MongoDB CRUD repository for ingested documents
│   │   ├── analysis_repo.py         # MongoDB CRUD repository for meeting analyses
│   │   ├── task_repo.py             # MongoDB CRUD repository for tasks & action items
│   │   └── workflow_repo.py         # MongoDB CRUD repository for workflow execution runs
│   └── schemas/
│       ├── __init__.py
│       ├── transcription.py         # Shared schemas for speech-to-text transcriptions
│       ├── document.py              # Shared schemas for document and pasted text ingestion
│       ├── analysis.py              # Shared schemas for structured meeting intelligence
│       ├── task.py                  # Schemas for tasks, follow-up plans, and exports
│       └── workflow.py              # Schemas for LangGraph workflow execution and status
├── tests/                           # Automated test suite (171 tests across 20 modules)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_schemas.py
│   ├── test_health.py
│   ├── test_whisper_service.py
│   ├── test_repository.py
│   ├── test_routes.py
│   ├── test_worker.py
│   ├── test_document_service.py
│   ├── test_document_repo.py
│   ├── test_document_routes.py
│   ├── test_llm_service.py
│   ├── test_meeting_analysis_service.py
│   ├── test_analysis_repo.py
│   ├── test_analysis_routes.py
│   ├── test_task_schemas.py
│   ├── test_task_repo.py
│   ├── test_task_service.py
│   ├── test_export_service.py
│   ├── test_task_routes.py
│   ├── test_workflow_schemas.py
│   ├── test_workflow_repo.py
│   ├── test_workflow_nodes.py
│   ├── test_workflow_engine.py
│   ├── test_workflow_routes.py
│   └── test_e2e_integration.py      # Multi-source end-to-end integration & resilience tests
├── .env.example                     # Example environment variables
├── .gitignore                       # Git ignore rules for secrets and temporary media
├── requirements.txt                 # Backend dependencies
└── README.md                        # Documentation
```

---

## 3. Setup and Installation

All primary commands below use **Windows PowerShell**.

### Step 1: Navigate to the backend directory

```powershell
cd backend
```

### Step 2: Create and activate a virtual environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1
```

> **Note**: If script execution is restricted on Windows, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Step 3: Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Environment Configuration

Copy `.env.example` to create your local `.env` file:

```powershell
Copy-Item .env.example .env
```

Key configuration parameters in `.env`:

```env
# Application Settings
APP_ENV=development
DEBUG=true

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=meeting_assistant

# File Upload Settings
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=100

# OpenAI Whisper Configuration (tiny, base, small, medium, large)
WHISPER_MODEL=small

# LLM Provider Configuration (Groq Cloud)
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_TIMEOUT_SECONDS=60.0

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 5. Running the Backend Server

Start the FastAPI application with `uvicorn`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will start at `http://127.0.0.1:8000`.

---

## 6. LangGraph Workflow Pipeline

The backend features an orchestrated **LangGraph StateGraph** pipeline connecting all intelligence features into an automated, deterministic workflow:

```
[ validate_input ]
        │ (valid)
        ▼
[ retrieve_source ]  ───► (fetch from transcription, document, or direct text)
        │
        ▼
[ meeting_analysis ] ───► (generate or reuse executive summary, decisions, risks)
        │
        ▼
[ action_item_extraction ] ──► (grounded task extraction with atomic replacement)
        │
        ▼
[ follow_up_planning ] ──► (categorized follow-up plan & AI recommendations)
        │
        ▼
[ finalize_workflow ] ──► (mark status completed with UTC timestamps)
```

Each stage is tracked in the MongoDB `workflows` collection with diagnostic error states if an error occurs.

---

## 7. API Endpoints Overview

### Health & System
- `GET /api/health` — Check server status, MongoDB connectivity, and Whisper engine state.

### Audio Transcription (`/api/transcriptions`)
- `POST /api/transcriptions/upload` — Upload recorded audio file and queue background Whisper transcription.
- `GET /api/transcriptions/` — Paginated list of transcription jobs.
- `GET /api/transcriptions/{record_id}` — Retrieve transcription record and generated text.
- `PATCH /api/transcriptions/{record_id}` — Update transcript text.
- `DELETE /api/transcriptions/{record_id}` — Delete a transcription record.

### Document & Text Ingestion (`/api/documents`)
- `POST /api/documents/upload` — Upload text-based `.pdf`, `.docx`, or `.txt` files.
- `POST /api/documents/text` — Submit raw pasted meeting notes or text as JSON.
- `GET /api/documents/` — Paginated list of ingested documents and text records.
- `GET /api/documents/{document_id}` — Retrieve full document text.
- `DELETE /api/documents/{document_id}` — Delete an ingested document record.

### AI Meeting Analysis (`/api/analysis`)
- `POST /api/analysis/` — Run AI analysis on meeting content.
- `GET /api/analysis/` — Paginated list of meeting analyses.
- `GET /api/analysis/{analysis_id}` — Retrieve complete meeting analysis report.
- `DELETE /api/analysis/{analysis_id}` — Delete an analysis report.

### Action Items & Task Management (`/api/tasks`)
- `POST /api/tasks/extract/{analysis_id}` — Extract action items from meeting analysis with `replace=true` support.
- `POST /api/tasks/` — Manually create a task.
- `GET /api/tasks/` — List tasks with filters (`analysis_id`, `status`, `priority`, `assignee`).
- `GET /api/tasks/{task_id}` — Retrieve single task details.
- `PATCH /api/tasks/{task_id}` — Update editable task fields.
- `PATCH /api/tasks/{task_id}/status` — Update task status.
- `DELETE /api/tasks/{task_id}` — Delete a task.
- `GET /api/tasks/analysis/{analysis_id}/plan` — Categorized follow-up plan.
- `GET /api/tasks/export` — Export action items as `json`, `csv`, or `markdown`.

### LangGraph Workflow Pipeline (`/api/workflows`)
- `POST /api/workflows/start` — Start end-to-end meeting workflow asynchronously (returns `202 Accepted` with workflow run ID).
- `POST /api/workflows/run-sync` — Execute meeting workflow synchronously and return the full consolidated result.
- `GET /api/workflows/{workflow_id}` — Poll workflow stage, progress, and status.
- `GET /api/workflows/{workflow_id}/result` — Retrieve full consolidated result (analysis + tasks + follow-up plan).
- `GET /api/workflows/` — Paginated list of workflow runs with `status` and `source_type` filters.
- `POST /api/workflows/{workflow_id}/retry` — Safely retry a failed workflow run.
- `DELETE /api/workflows/{workflow_id}` — Delete a workflow run record.

---

## 8. Interactive Documentation & Deep Guides

- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Comprehensive Engineering Guides
- [API Reference Guide (All 32 Operations & Endpoints)](./docs/API_REFERENCE.md)
- [Application Workflow & Architecture Guide](./docs/API_WORKFLOW_GUIDE.md)
- [Frontend React API Integration Guide](./docs/FRONTEND_API_INTEGRATION.md)

---

## 9. Automated Testing & Reliability Notes

### Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
pytest -v
```

All **171 automated unit and end-to-end integration tests** across **20 test modules** execute completely in isolation with 100% mocked external dependencies (`mongomock`, mocked Whisper inference, mocked Groq client).

### Real vs. Mocked Execution

| Environment | Database | Whisper Transcription | LLM Intelligence (Groq) |
| :--- | :--- | :--- | :--- |
| **Automated Tests (`pytest`)** | In-Memory `mongomock` | Mocked transcription responses | Mocked structured JSON responses |
| **Local Development / Live** | MongoDB (`mongodb://localhost:27017`) | Local OpenAI Whisper (`small` model) via FFmpeg | Groq Cloud API (`llama-3.3-70b-versatile`) |

### Background Worker Resilience

- Asynchronous workflows and audio transcriptions use FastAPI `BackgroundTasks` running in the backend server process.
- **Process Lifecycle Limitation**: In-flight background jobs execute in memory; if the server process restarts unexpectedly, in-flight jobs are marked with diagnostic error states or require a `/retry` call. For distributed high-throughput enterprise deployments, a dedicated task queue (e.g. Celery / Redis Queue) can be integrated seamlessly with the existing repository and engine abstraction.

