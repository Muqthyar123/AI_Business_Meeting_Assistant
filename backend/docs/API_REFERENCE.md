# AI Business Meeting Assistant - Complete API Reference

> **Base URL**: `http://127.0.0.1:8000`  
> **API Prefix**: `/api`  
> **OpenAPI Specification**: 3.1.0  
> **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
> **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 1. Summary of API Groups & Endpoints

| Group | Method | Endpoint Path | Summary | Operation Type |
| :--- | :---: | :--- | :--- | :---: |
| **Health & Root** | `GET` | `/` | Root API navigation metadata | Sync |
| **Health & Root** | `GET` | `/api/health` | System health check (API, MongoDB, Whisper) | Sync |
| **Transcriptions** | `POST` | `/api/transcriptions/upload` | Upload recorded audio for transcription | Async (Background) |
| **Transcriptions** | `GET` | `/api/transcriptions/` | Paginated transcription history listing | Sync |
| **Transcriptions** | `GET` | `/api/transcriptions/{record_id}` | Retrieve single transcription details & transcript | Sync |
| **Transcriptions** | `PATCH` | `/api/transcriptions/{record_id}` | Edit transcript text | Sync |
| **Transcriptions** | `DELETE` | `/api/transcriptions/{record_id}` | Delete transcription record | Sync |
| **Documents** | `POST` | `/api/documents/upload` | Ingest PDF, DOCX, or TXT document | Sync |
| **Documents** | `POST` | `/api/documents/text` | Ingest pasted meeting notes / raw text | Sync |
| **Documents** | `GET` | `/api/documents/` | Paginated ingested documents listing | Sync |
| **Documents** | `GET` | `/api/documents/{document_id}` | Retrieve single document details & extracted text | Sync |
| **Documents** | `DELETE` | `/api/documents/{document_id}` | Delete ingested document record | Sync |
| **Meeting Analysis** | `POST` | `/api/analysis/` | Generate structured AI meeting intelligence | Sync (LLM) |
| **Meeting Analysis** | `GET` | `/api/analysis/` | Paginated meeting analyses listing | Sync |
| **Meeting Analysis** | `GET` | `/api/analysis/{analysis_id}` | Retrieve single meeting analysis report | Sync |
| **Meeting Analysis** | `DELETE` | `/api/analysis/{analysis_id}` | Delete meeting analysis report | Sync |
| **Tasks & Planning** | `POST` | `/api/tasks/extract/{analysis_id}` | Extract grounded action items with replacement | Sync (LLM) |
| **Tasks & Planning** | `POST` | `/api/tasks/` | Manually create action item | Sync |
| **Tasks & Planning** | `GET` | `/api/tasks/` | List action items with status/priority/owner filters | Sync |
| **Tasks & Planning** | `GET` | `/api/tasks/export` | Export tasks/plan as JSON, CSV, or Markdown | Sync |
| **Tasks & Planning** | `GET` | `/api/tasks/analysis/{analysis_id}/plan` | Categorized follow-up plan generation | Sync |
| **Tasks & Planning** | `GET` | `/api/tasks/{task_id}` | Retrieve single task record | Sync |
| **Tasks & Planning** | `PATCH` | `/api/tasks/{task_id}` | Update task details (assignee, priority, due date) | Sync |
| **Tasks & Planning** | `PATCH` | `/api/tasks/{task_id}/status` | Update task status | Sync |
| **Tasks & Planning** | `DELETE` | `/api/tasks/{task_id}` | Delete task record | Sync |
| **Workflows** | `POST` | `/api/workflows/start` | Launch LangGraph meeting pipeline asynchronously | Async (Background) |
| **Workflows** | `POST` | `/api/workflows/run-sync` | Execute LangGraph meeting pipeline synchronously | Sync (Pipeline) |
| **Workflows** | `GET` | `/api/workflows/` | Paginated workflow runs listing | Sync |
| **Workflows** | `GET` | `/api/workflows/{workflow_id}` | Poll workflow execution stage & status | Sync |
| **Workflows** | `GET` | `/api/workflows/{workflow_id}/result` | Retrieve consolidated workflow result | Sync |
| **Workflows** | `POST` | `/api/workflows/{workflow_id}/retry` | Safely retry failed workflow run | Async (Background) |
| **Workflows** | `DELETE` | `/api/workflows/{workflow_id}` | Delete workflow execution record | Sync |

---

## 2. Health & Root Endpoints

### 2.1 `GET /` — Root Welcome Endpoint
- **Group**: Root
- **Method**: `GET`
- **Path**: `/`
- **Operation Summary**: Root Welcome Endpoint
- **Description**: Returns top-level API metadata and documentation URLs.
- **Authentication**: None
- **Parameters**: None
- **Request Body**: None
- **Response Model**: `dict`
- **Example Response (`200 OK`)**:
  ```json
  {
    "name": "AI Business Meeting Assistant",
    "version": "0.1.0",
    "docs": "/docs",
    "health": "/api/health",
    "api_prefix": "/api"
  }
  ```
- **Internal Processing**: Returns static metadata dictionary from `Settings`.
- **Database / LLM**: None.

---

### 2.2 `GET /api/health` — System Health Check
- **Group**: Health
- **Method**: `GET`
- **Path**: `/api/health`
- **Operation Summary**: API and Database Health Check
- **Description**: Evaluates connectivity to MongoDB and verifies the Whisper model engine state.
- **Authentication**: None
- **Parameters**: None
- **Response Model**: `HealthResponse`
- **Response Status Codes**:
  - `200 OK`: Database connected (`status="healthy"`).
  - `503 Service Unavailable`: Database disconnected (`status="degraded"`).
- **Example Response (`200 OK`)**:
  ```json
  {
    "status": "healthy",
    "api_status": "running",
    "database_status": "connected",
    "whisper_status": "loaded",
    "whisper_model": "small",
    "version": "0.1.0"
  }
  ```
- **Internal Services**: `app.database.ping_database()`, `app.services.whisper_service.get_whisper_service()`.
- **Database Collection**: None (admin `ping` command executed).

---

## 3. Transcriptions Endpoints (`/api/transcriptions`)

### 3.1 `POST /api/transcriptions/upload` — Upload Recorded Audio
- **Group**: Transcriptions
- **Method**: `POST`
- **Path**: `/api/transcriptions/upload`
- **Summary**: Upload recorded audio for transcription
- **Description**: Accepts audio files (`.wav`, `.mp3`, `.m4a`, `.mp4`, `.webm`, `.ogg`, `.flac`, `.wma`), streams to disk buffer, inserts a `queued` transcription document in MongoDB, and dispatches a background Whisper transcription worker.
- **Request Content-Type**: `multipart/form-data`
- **Form Parameters**:
  | Field | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `file` | `UploadFile` | **Yes** | Binary audio stream |
  | `language` | `string` | No | Optional ISO 639-1 language code (e.g., `'en'`, `'es'`) |
- **Validation Rules**:
  - Empty files (0 bytes) $\to$ `400 Bad Request`.
  - Unsupported extension $\to$ `400 Bad Request`.
  - File size $> 100\text{MB}$ (configured via `MAX_UPLOAD_SIZE_MB`) $\to$ `413 Content Too Large`.
- **Response Model**: `TranscriptionCreateResponse`
- **Response Status Codes**:
  - `202 Accepted`: Audio uploaded and queued.
  - `400 Bad Request`: Empty file or unsupported format.
  - `413 Content Too Large`: File exceeds size limit.
  - `503 Service Unavailable`: Database unavailable.
- **Example Response (`202 Accepted`)**:
  ```json
  {
    "job_id": "6ac8c52f9a482ef53036cc5f",
    "status": "queued",
    "message": "Audio accepted for transcription"
  }
  ```
- **Internal Services**: `transcription_worker.process_transcription_job` via FastAPI `BackgroundTasks`.
- **Database Collection**: `transcriptions` (`insert_one`).
- **Side Effects**: Writes temporary audio file to `uploads/`, deleted upon worker completion.

---

### 3.2 `GET /api/transcriptions/` — List Transcription History
- **Group**: Transcriptions
- **Method**: `GET`
- **Path**: `/api/transcriptions/`
- **Summary**: List transcription history
- **Query Parameters**:
  | Param | Type | Default | Description |
  | :--- | :---: | :---: | :--- |
  | `page` | `int` | `1` | 1-indexed page number |
  | `page_size` | `int` | `20` | Max records per page ($1 \le \text{page\_size} \le 100$) |
  | `status` | `TranscriptionStatus` | `null` | Optional filter: `queued`, `processing`, `completed`, `failed` |
- **Response Model**: `TranscriptionListResponse`
- **Example Response (`200 OK`)**:
  ```json
  {
    "items": [
      {
        "id": "6ac8c52f9a482ef53036cc5f",
        "original_filename": "sprint_planning.wav",
        "file_format": "wav",
        "file_size_bytes": 1048576,
        "status": "completed",
        "transcript_text": "Priya confirmed the release date is October 20.",
        "detected_language": "en",
        "audio_duration": 45.2,
        "whisper_model": "small",
        "error_message": null,
        "created_at": "2026-10-09T15:00:00Z",
        "updated_at": "2026-10-09T15:00:15Z",
        "completed_at": "2026-10-09T15:00:15Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```
- **Database Collection**: `transcriptions` (`find`, `count_documents`, sorted by `created_at` descending).

---

### 3.3 `GET /api/transcriptions/{record_id}` — Get Transcription Details
- **Group**: Transcriptions
- **Method**: `GET`
- **Path**: `/api/transcriptions/{record_id}`
- **Path Parameters**: `record_id: str` (24-hex MongoDB ObjectId).
- **Response Model**: `TranscriptionResponse`
- **Response Status Codes**:
  - `200 OK`: Record found.
  - `404 Not Found`: Record ID not found or invalid format.

---

### 3.4 `PATCH /api/transcriptions/{record_id}` — Update Transcript Text
- **Group**: Transcriptions
- **Method**: `PATCH`
- **Path**: `/api/transcriptions/{record_id}`
- **Request Body**: `TranscriptionUpdateRequest`
  ```json
  {
    "transcript_text": "Corrected transcript text from user review."
  }
  ```
- **Response Model**: `TranscriptionResponse`
- **Response Status Codes**:
  - `200 OK`: Updated.
  - `404 Not Found`: Record not found.

---

### 3.5 `DELETE /api/transcriptions/{record_id}` — Delete Transcription
- **Group**: Transcriptions
- **Method**: `DELETE`
- **Path**: `/api/transcriptions/{record_id}`
- **Response Status Codes**:
  - `204 No Content`: Successfully deleted.
  - `404 Not Found`: Record not found.

---

## 4. Documents Endpoints (`/api/documents`)

### 4.1 `POST /api/documents/upload` — Ingest Document File
- **Group**: Documents
- **Method**: `POST`
- **Path**: `/api/documents/upload`
- **Description**: Extracts and normalizes text synchronously from `.pdf`, `.docx`, or `.txt` files.
- **Request Content-Type**: `multipart/form-data`
- **Form Parameters**:
  | Field | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `file` | `UploadFile` | **Yes** | Text-based document file |
  | `title` | `string` | No | Optional human-readable title |
- **Validation Rules**:
  - Unsupported extension $\to$ `400 Bad Request`.
  - Empty file (0 bytes) $\to$ `400 Bad Request`.
  - Scanned PDF without extractable text $\to$ `422 Unprocessable Content`.
  - Corrupted DOCX/PDF $\to$ `422 Unprocessable Content`.
- **Response Model**: `DocumentResponse`
- **Example Response (`201 Created`)**:
  ```json
  {
    "id": "6ac8c52f9a482ef53036cc61",
    "source_type": "txt",
    "title": "Incident Post-Mortem",
    "original_filename": "postmortem.txt",
    "file_format": "txt",
    "file_size_bytes": 455,
    "text_content": "Incident Post-Mortem & Action Items - Service Outage...",
    "character_count": 455,
    "word_count": 69,
    "status": "completed",
    "error_message": null,
    "created_at": "2026-10-09T15:10:00Z",
    "updated_at": "2026-10-09T15:10:00Z"
  }
  ```

---

### 4.2 `POST /api/documents/text` — Ingest Pasted Notes
- **Group**: Documents
- **Method**: `POST`
- **Path**: `/api/documents/text`
- **Request Body**: `PastedTextInput`
  ```json
  {
    "text": "Sprint planning meeting notes. Alex agreed to complete the authentication API by Friday.",
    "title": "Sprint 42 Notes"
  }
  ```
- **Response Model**: `DocumentResponse` (`source_type="pasted_text"`)
- **Response Status Codes**: `201 Created`, `400 Bad Request`.

---

### 4.3 `GET /api/documents/` — List Ingested Documents
- **Group**: Documents
- **Method**: `GET`
- **Path**: `/api/documents/`
- **Query Parameters**: `page: int = 1`, `page_size: int = 20`, `source_type: Optional[DocumentSourceType]` (`pdf`, `docx`, `txt`, `pasted_text`).
- **Response Model**: `DocumentListResponse`.

---

### 4.4 `GET /api/documents/{document_id}` — Get Document Details
- **Group**: Documents
- **Method**: `GET`
- **Path**: `/api/documents/{document_id}`
- **Response Model**: `DocumentResponse`. Status: `200 OK` or `404 Not Found`.

---

### 4.5 `DELETE /api/documents/{document_id}` — Delete Document
- **Group**: Documents
- **Method**: `DELETE`
- **Path**: `/api/documents/{document_id}`
- **Response Status**: `204 No Content` or `404 Not Found`.

---

## 5. Meeting Analysis Endpoints (`/api/analysis`)

### 5.1 `POST /api/analysis/` — Generate AI Meeting Analysis
- **Group**: Meeting Analysis
- **Method**: `POST`
- **Path**: `/api/analysis/`
- **Description**: Executes LLM meeting intelligence extraction on a completed transcription, document, or raw text.
- **Request Body**: `AnalysisCreateRequest`
  ```json
  {
    "source_type": "transcription",
    "source_id": "6ac8c52f9a482ef53036cc5f",
    "text": null,
    "title": "Sprint 42 Analysis",
    "force_reanalyze": false
  }
  ```
- **Validation Rules**:
  - `source_type="transcription"` requires `source_id` pointing to a `completed` transcription record.
  - `source_type="document"` requires `source_id` pointing to an existing document record.
  - `source_type="direct_text"` requires non-empty `text`.
- **Response Model**: `AnalysisResponse`
- **Example Response (`201 Created`)**:
  ```json
  {
    "id": "6ac8c5329a482ef53036cc60",
    "source_id": "6ac8c52f9a482ef53036cc5f",
    "source_type": "transcription",
    "title": "Sprint 42 Analysis",
    "executive_summary": "The team reviewed Q4 commitments and confirmed deployment milestones.",
    "meeting_purpose": "Align on sprint deliverables and allocate ownership.",
    "key_discussion_points": [
      "Authentication API delivery timeline",
      "Dashboard performance bottlenecks"
    ],
    "decisions_made": [
      "Freeze feature work on November 1st",
      "Deploy staging payment gateway by Friday"
    ],
    "risks_and_blockers": [
      "Database index rebuild latency"
    ],
    "unresolved_questions": [
      "Who will prepare the disaster recovery runbook?"
    ],
    "topics_and_themes": [
      "Infrastructure",
      "Security"
    ],
    "llm_provider": "groq",
    "llm_model": "qwen/qwen3.8-27b",
    "status": "completed",
    "error_message": null,
    "created_at": "2026-10-09T15:20:00Z",
    "updated_at": "2026-10-09T15:20:00Z"
  }
  ```

---

### 5.2 `GET /api/analysis/` — List Meeting Analyses
- **Query Parameters**: `page: int = 1`, `page_size: int = 20`, `source_type: Optional[AnalysisSourceType]`.
- **Response Model**: `AnalysisListResponse`.

---

### 5.3 `GET /api/analysis/{analysis_id}` — Get Analysis Details
- **Path Parameters**: `analysis_id: str`.
- **Response Model**: `AnalysisResponse`. Status: `200 OK` or `404 Not Found`.

---

### 5.4 `DELETE /api/analysis/{analysis_id}` — Delete Analysis
- **Path Parameters**: `analysis_id: str`.
- **Response Status**: `204 No Content` or `404 Not Found`.
- **Note**: Deleting an analysis record does **not** delete the source transcription or document.

---

## 6. Tasks and Follow-Up Planning Endpoints (`/api/tasks`)

### 6.1 `POST /api/tasks/extract/{analysis_id}` — Extract Action Items
- **Group**: Tasks
- **Method**: `POST`
- **Path**: `/api/tasks/extract/{analysis_id}`
- **Query Parameters**: `replace: bool = true` (If `true`, removes existing tasks for this analysis before inserting new ones to avoid duplicates).
- **Response Model**: `List[TaskResponse]`
- **Example Response (`201 Created`)**:
  ```json
  [
    {
      "id": "6ac8c5359a482ef53036cc62",
      "analysis_id": "6ac8c5329a482ef53036cc60",
      "description": "Deploy payment gateway to staging environment",
      "assignee": "Sarah Chen",
      "has_missing_assignee": false,
      "due_date": "by Friday",
      "priority": "high",
      "status": "pending",
      "dependencies": ["Database index rebuild"],
      "evidence_excerpt": "Sarah agreed to deploy the new auth service by Friday.",
      "created_at": "2026-10-09T15:22:00Z",
      "updated_at": "2026-10-09T15:22:00Z"
    }
  ]
  ```

---

### 6.2 `POST /api/tasks/` — Manually Create Action Item
- **Request Body**: `TaskCreateRequest`
  ```json
  {
    "analysis_id": "6ac8c5329a482ef53036cc60",
    "description": "Prepare disaster recovery runbook",
    "assignee": "DevOps Lead",
    "has_missing_assignee": false,
    "due_date": "2026-10-25",
    "priority": "medium",
    "status": "pending",
    "dependencies": [],
    "evidence_excerpt": null
  }
  ```
- **Response Model**: `TaskResponse` (`201 Created`).

---

### 6.3 `GET /api/tasks/` — List Filtered Tasks
- **Query Parameters**:
  - `analysis_id: Optional[str]`
  - `status: Optional[TaskStatus]` (`pending`, `in_progress`, `completed`, `cancelled`)
  - `priority: Optional[TaskPriority]` (`low`, `medium`, `high`, `unknown`)
  - `assignee: Optional[str]`
  - `page: int = 1`
  - `page_size: int = 50`
- **Response Model**: `TaskListResponse`.

---

### 6.4 `GET /api/tasks/export` — Export Tasks & Follow-Up Plan
- **Query Parameters**:
  - `format: TaskExportFormat = json` (`json`, `csv`, `markdown`)
  - `analysis_id: Optional[str]`
- **Response Content Types**:
  - `json`: `application/json; charset=utf-8` (Download attachment `tasks_<id>.json`)
  - `csv`: `text/csv; charset=utf-8` (Download attachment `tasks_<id>.csv`)
  - `markdown`: `text/markdown; charset=utf-8` (Download attachment `tasks_plan_<id>.md`)

---

### 6.5 `GET /api/tasks/analysis/{analysis_id}/plan` — Get Follow-Up Plan
- **Path Parameters**: `analysis_id: str`.
- **Response Model**: `FollowUpPlanResponse`
- **Categorization**:
  - `immediate_actions`: High priority tasks.
  - `upcoming_tasks`: Tasks with scheduled deadlines.
  - `clarification_needed`: Tasks with missing owners or missing deadlines.
  - `blockers_and_dependencies`: Blocked tasks.
  - `pending_decisions`: Open risks and unresolved questions.
  - `ai_suggestions`: Contextual advice to drive accountability.

---

### 6.6 `GET /api/tasks/{task_id}`, `PATCH /api/tasks/{task_id}`, `PATCH /api/tasks/{task_id}/status`, `DELETE /api/tasks/{task_id}`
- Standard CRUD endpoints for individual task lifecycle management.

---

## 7. LangGraph Workflows Endpoints (`/api/workflows`)

### 7.1 `POST /api/workflows/start` — Start Asynchronous Workflow
- **Method**: `POST`
- **Path**: `/api/workflows/start`
- **Status Code**: `202 Accepted`
- **Request Body**: `WorkflowStartRequest`
  ```json
  {
    "source_type": "transcription",
    "source_id": "6ac8c52f9a482ef53036cc5f",
    "text": null,
    "title": "Executive Strategy Sync",
    "force_reanalyze": false
  }
  ```
- **Response Model**: `WorkflowStatusResponse` (`status="queued"`, `current_stage="queued"`).
- **Processing**: Dispatches LangGraph workflow in a non-blocking background task.

---

### 7.2 `POST /api/workflows/run-sync` — Execute Synchronous Workflow
- **Method**: `POST`
- **Path**: `/api/workflows/run-sync`
- **Status Code**: `200 OK`
- **Request Body**: `WorkflowStartRequest`
- **Response Model**: `WorkflowResultResponse`
- **Example Response (`200 OK`)**:
  ```json
  {
    "id": "6ac8c52f9a482ef53036cc5f",
    "source_type": "direct_text",
    "source_id": null,
    "title": "Website Launch Planning Meeting",
    "current_stage": "finalized",
    "status": "completed",
    "analysis": {
      "id": "6ac8c5329a482ef53036cc60",
      "executive_summary": "Priya confirmed the website launches on October 20...",
      "meeting_purpose": "To confirm the website launch date and assign tasks.",
      "decisions_made": ["Website launch date confirmed for October 20, 2026."],
      "risks_and_blockers": [],
      "unresolved_questions": ["Whether additional server resources are required."],
      "topics_and_themes": ["Launch", "Engineering"],
      "llm_provider": "groq",
      "llm_model": "qwen/qwen3.8-27b",
      "status": "completed",
      "created_at": "2026-10-09T16:13:00Z",
      "updated_at": "2026-10-09T16:13:00Z"
    },
    "tasks": [
      {
        "id": "6ac8c5359a482ef53036cc62",
        "analysis_id": "6ac8c5329a482ef53036cc60",
        "description": "Complete the authentication API",
        "assignee": "Rahul",
        "has_missing_assignee": false,
        "due_date": "October 12, 2026",
        "priority": "high",
        "status": "pending",
        "dependencies": [],
        "evidence_excerpt": "Rahul will complete the authentication API by October 12, 2026.",
        "created_at": "2026-10-09T16:13:00Z",
        "updated_at": "2026-10-09T16:13:00Z"
      }
    ],
    "follow_up_plan": {
      "analysis_id": "6ac8c5329a482ef53036cc60",
      "immediate_actions": [],
      "upcoming_tasks": [],
      "clarification_needed": [],
      "blockers_and_dependencies": [],
      "pending_decisions": ["Whether additional server resources are required."],
      "ai_suggestions": ["All action items have assigned owners and targets."],
      "total_tasks": 1,
      "generated_at": "2026-10-09T16:13:00Z"
    },
    "error_stage": null,
    "error_message": null,
    "created_at": "2026-10-09T16:12:55Z",
    "updated_at": "2026-10-09T16:13:01Z",
    "completed_at": "2026-10-09T16:13:01Z"
  }
  ```

---

### 7.3 `GET /api/workflows/{workflow_id}` — Poll Workflow Status
- **Method**: `GET`
- **Path**: `/api/workflows/{workflow_id}`
- **Response Model**: `WorkflowStatusResponse`
- **Polled Fields**: `status` (`queued`, `processing`, `completed`, `failed`), `current_stage` (`queued`, `input_validation`, `source_retrieval`, `meeting_analysis`, `action_item_extraction`, `follow_up_planning`, `finalized`, `failed`).

---

### 7.4 `GET /api/workflows/{workflow_id}/result` — Get Consolidated Result
- **Method**: `GET`
- **Path**: `/api/workflows/{workflow_id}/result`
- **Response Model**: `WorkflowResultResponse`.

---

### 7.5 `POST /api/workflows/{workflow_id}/retry` — Retry Failed Workflow
- **Method**: `POST`
- **Path**: `/api/workflows/{workflow_id}/retry`
- **Status Code**: `202 Accepted`
- **Validation**: Cannot retry a workflow whose current status is `processing` (`400 Bad Request`).

---

### 7.6 `DELETE /api/workflows/{workflow_id}` — Delete Workflow Record
- **Method**: `DELETE`
- **Path**: `/api/workflows/{workflow_id}`
- **Status Code**: `204 No Content`.
- **Note**: Deletes only the workflow execution tracking record from the `workflows` collection. Analysis, task, document, and audio records are preserved.
