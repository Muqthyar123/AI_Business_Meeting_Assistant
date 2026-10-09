# AI Business Meeting Assistant
### React 18 Web App, STS Desktop Voice Assistant & FastAPI + LangGraph AI Pipeline

An end-to-end, production-quality AI business meeting intelligence system combining:
1. **React 18 + Vite + TailwindCSS Web Application** (`frontend/`) — Executive dashboard, meeting workspace, audio/doc ingestion, transcript editor, AI insights, decision logs, Kanban task execution board, and report exports.
2. **Lightweight Desktop Voice Assistant** (`desktop/` & root `main.py` / `GUI.py`) — Live speech-to-text with `faster-whisper`, Windows WASAPI system-audio loopback mixer, floating widget, and target application auto-pasting.
3. **Production-Grade FastAPI Backend** (`backend/`) — MongoDB Atlas persistence, Groq Cloud LLM reasoning (`qwen/qwen3.8-27b`), OpenAI Whisper audio processing, and LangGraph multi-node workflow orchestration.

---

## 1. System Architecture & Capabilities

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        WEB APP & DESKTOP CLIENTS                       │
│                                                                        │
│  ┌───────────────────────┐  ┌──────────────────────┐  ┌─────────────┐  │
│  │ React Web Application │  │ Live Meeting Desktop │  │ Dictation   │  │
│  │ (Vite / React 18 / TS)│  │ (Mic + WASAPI Audio) │  │ (Right-Shift│  │
│  └──────────┬────────────┘  └──────────┬───────────┘  └──────┬──────┘  │
└─────────────┼──────────────────────────┼─────────────────────┼─────────┘
              │                          │                     │
              ▼                          ▼                     ▼
     REST API Requests          POST /api/workflows/run-sync  Clipboard
              │                          │                     Injection
              └──────────────────────────┼─────────────────────┘
                                         │
┌────────────────────────────────────────┼───────────────────────────────┐
│                 FASTAPI + LANGGRAPH BACKEND                            │
│                                        ▼                               │
│                              [ Input Validation Node ]                 │
│                                        │                               │
│                              [ Source Retrieval Node ]                 │
│                              (Audio / Doc / Direct Text)               │
│                                        │                               │
│                              [ Meeting Analysis Node ]                 │
│                              (Groq Cloud LLM Engine)                   │
│                                        │                               │
│                              [ Action Items Node ]                     │
│                              (Grounded Task Extraction)                │
│                                        │                               │
│                              [ Follow-up Plan Node ]                   │
│                              (Milestone Planning Graph)                │
│                                        │                               │
│                              [ MongoDB Atlas Storage ]                 │
│                              (Collections: analyses, tasks,            │
│                               transcriptions, documents, workflows)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Features

### A. Web Application (`frontend/`)
- **Executive Dashboard**: Real-time KPI metrics, action item completion distribution, decision counts, and recent meeting activity.
- **Unified Meetings Workspace**: Multi-modal ingestion supporting:
  - **Audio Recording Uploads** (`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.webm`) processed via Whisper.
  - **Document File Ingestion** (`.pdf`, `.docx`, `.txt`) with text extraction and normalization.
  - **Manual / Direct Transcript Bar** for pasting notes from Zoom, Teams, Meet, Otter, etc.
- **Meeting Intelligence Hub**: Interactive tabs for **Overview**, **Transcript Editor**, **AI Insights** (Executive Summary, Discussion Points, Themes, Risks, Unresolved Questions), **Decisions**, **Action Items**, and **Follow-up Roadmap**.
- **Action Item Execution Board**: Filterable by status (`To Do`, `In Progress`, `Blocked`, `Completed`), priority (`Urgent`, `High`, `Medium`, `Low`), assignee, and meeting source, with interactive Kanban and table views.
- **Decisions Log**: Searchable catalog of confirmed organizational agreements with source evidence excerpts.
- **Follow-up Roadmap**: Chronological milestone sequences turning meeting commitments into scheduled deliverables.
- **Export Engine**: Export meetings to **PDF**, **Markdown**, **CSV**, **JSON**, or raw **TXT**.
- **System Health Monitor**: Live telemetry for MongoDB Atlas, Whisper, and Groq LLM availability.

### B. Live Meeting Desktop Assistant (`desktop/`)
- **Continuous Speech Capture**: Dual audio mixer capturing local speaker microphone + remote participants via Windows WASAPI loopback.
- **Incremental Pause Segmentation**: Detects natural speech pauses (default `2.0s`), transcribes segments in background, and appends to an ordered cumulative meeting panel.
- **Buffer Flushing**: Flushes pending audio on meeting finish so concluding remarks are never truncated.
- **Local Fallback Recovery**: Automatically backs up raw transcripts locally to prevent data loss.

### C. General Dictation Mode
- **Instant Hotkey**: Press **Right Shift** to dictate anywhere in Windows.
- **Smart Target Pasting**: Refocuses previous application window and injects transcribed text.

---

## 3. Installation & Prerequisites

### Prerequisites
- **Windows 10 / 11**
- **Node.js 18+** & **npm**
- **Python 3.10+** (Python 3.11 / 3.12 recommended)
- **FFmpeg** (Required for audio decoding)
- **MongoDB Atlas** connection URI
- **Groq Cloud API Key**

### 1. Setup Backend & Desktop Environment

```powershell
# 1. Install FFmpeg
winget install Gyan.FFmpeg

# 2. Activate Python Virtual Environment
.\backend\.venv\Scripts\Activate.ps1

# 3. Install Python Dependencies
pip install -r backend/requirements.txt
pip install -r requirements-desktop.txt
```

### 2. Setup Frontend Environment

```powershell
cd frontend
npm install
cd ..
```

---

## 4. Configuration (`.env`)

Create or update `.env` in the root or `backend/` directory:

```env
# Backend Configuration
PORT=8000
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=AIBusinessMeetingAssistant

# Groq Cloud LLM Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b

# Whisper Speech-to-Text Configuration
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# Desktop Client Configuration
BACKEND_URL=http://127.0.0.1:8000
AUDIO_SOURCE=both
```

---

## 5. Running the Application

### Step 1: Start the FastAPI Backend Server
```powershell
cd backend
..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Step 2: Start the React Web Application
In a separate terminal:
```powershell
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Step 3 (Optional): Start the Desktop Voice Assistant
In a separate terminal:
```powershell
.\backend\.venv\Scripts\python.exe main.py --meeting
```

---

## 6. Automated Testing

Run all **189 tests** across backend and desktop suites:

```powershell
pytest backend/tests/ tests/ -v
```

Build and test the React frontend:
```powershell
cd frontend
npm run build
```

---

## 7. API Summary

| Group | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **Health** | `GET` | `/api/health` | Live database and Whisper model connectivity check |
| **Transcriptions** | `POST` | `/api/transcriptions/upload` | Upload audio for asynchronous Whisper transcription |
| **Transcriptions** | `GET` | `/api/transcriptions/` | Paginated transcription history listing |
| **Transcriptions** | `GET` | `/api/transcriptions/{id}` | Retrieve transcription status and text |
| **Documents** | `POST` | `/api/documents/upload` | Extract text from PDF, DOCX, TXT files |
| **Documents** | `POST` | `/api/documents/text` | Ingest pasted meeting notes and transcripts |
| **Analysis** | `POST` | `/api/analysis/` | Generate structured AI intelligence from source |
| **Analysis** | `GET` | `/api/analysis/` | List meeting analyses |
| **Tasks** | `POST` | `/api/tasks/extract/{id}` | Extract grounded action items |
| **Tasks** | `GET` | `/api/tasks/` | List action items with status/priority filters |
| **Tasks** | `GET` | `/api/tasks/analysis/{id}/plan` | Generate categorized follow-up milestone plan |
| **Tasks** | `GET` | `/api/tasks/export` | Export tasks/plan as JSON, CSV, or Markdown |
| **Workflows** | `POST` | `/api/workflows/run-sync` | Execute end-to-end LangGraph meeting pipeline |
| **Workflows** | `POST` | `/api/workflows/start` | Launch asynchronous LangGraph meeting pipeline |
| **Workflows** | `GET` | `/api/workflows/{id}` | Poll workflow execution stages |

---

## 8. License & Privacy Policy

- **Zero Cloud Training**: Audio and transcripts are processed privately with zero data retention for training.
- **Local Audio Processing**: Speech is converted locally via Whisper.
- **Participant Consent**: Always ensure compliance with recording consent regulations in your jurisdiction.
