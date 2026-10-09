# AI Business Meeting Assistant - Frontend API Integration Guide

This guide is designed for the React / Vite frontend engineer. It outlines how to integrate the backend REST API, handle asynchronous jobs, manage data models, and render meeting intelligence UI components.

---

## 1. Network & CORS Configuration

- **API Base URL**: `http://127.0.0.1:8000` (or `http://localhost:8000`)
- **API Prefix**: `/api`
- **Allowed CORS Origins**:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- **Global Headers**:
  - For JSON requests: `Content-Type: application/json`
  - For Multipart file uploads: Do **not** set `Content-Type` manually (let the browser / Axios set the boundary).

---

## 2. User Action to API Mapping Table

| User Action in UI | HTTP Method | Endpoint Path | Payload / Query | Key Response Data |
| :--- | :---: | :--- | :--- | :--- |
| **Check System Status** | `GET` | `/api/health` | None | `database_status`, `whisper_status` |
| **Upload Audio File** | `POST` | `/api/transcriptions/upload` | `FormData: { file, language }` | `job_id`, `status: "queued"` |
| **Poll Audio Progress** | `GET` | `/api/transcriptions/{job_id}` | None | `status`, `transcript_text` |
| **Upload Document** | `POST` | `/api/documents/upload` | `FormData: { file, title }` | `id`, `text_content`, `word_count` |
| **Submit Pasted Notes** | `POST` | `/api/documents/text` | `{ text, title }` | `id`, `text_content`, `character_count` |
| **Run Synchronous Workflow** | `POST` | `/api/workflows/run-sync` | `{ source_type, source_id, text, title }` | Full `WorkflowResultResponse` |
| **Start Asynchronous Workflow** | `POST` | `/api/workflows/start` | `{ source_type, source_id, text, title }` | `id`, `status: "queued"` |
| **Poll Workflow Status** | `GET` | `/api/workflows/{workflow_id}` | None | `current_stage`, `status`, `error_message` |
| **Get Workflow Result** | `GET` | `/api/workflows/{workflow_id}/result` | None | `analysis`, `tasks`, `follow_up_plan` |
| **Retry Failed Workflow** | `POST` | `/api/workflows/{workflow_id}/retry` | None | `status: "queued"` |
| **Toggle Task Status** | `PATCH` | `/api/tasks/{task_id}/status` | `{ status: "completed" }` | Updated `TaskResponse` |
| **Edit Task Details** | `PATCH` | `/api/tasks/{task_id}` | `{ assignee, priority, due_date }` | Updated `TaskResponse` |
| **Add Manual Task** | `POST` | `/api/tasks/` | `TaskCreateRequest` | Created `TaskResponse` |
| **Fetch Follow-Up Plan** | `GET` | `/api/tasks/analysis/{analysis_id}/plan` | None | `FollowUpPlanResponse` |
| **Download Export File** | `GET` | `/api/tasks/export` | `?format=json&analysis_id=...` | File Attachment Download |

---

## 3. TypeScript Interfaces

```typescript
// --- Enums ---
export type TranscriptionStatus = 'queued' | 'processing' | 'completed' | 'failed';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'unknown';
export type WorkflowStatus = 'queued' | 'processing' | 'completed' | 'failed';
export type WorkflowStage =
  | 'queued'
  | 'input_validation'
  | 'source_retrieval'
  | 'meeting_analysis'
  | 'action_item_extraction'
  | 'follow_up_planning'
  | 'finalized'
  | 'failed';

// --- Transcriptions ---
export interface TranscriptionResponse {
  id: string;
  original_filename: string;
  file_format: string;
  file_size_bytes: number;
  status: TranscriptionStatus;
  transcript_text: string | null;
  detected_language: string | null;
  audio_duration: number | null;
  whisper_model: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

// --- Documents ---
export interface DocumentResponse {
  id: string;
  source_type: 'pdf' | 'docx' | 'txt' | 'pasted_text';
  title: string | null;
  original_filename: string | null;
  file_format: string | null;
  file_size_bytes: number;
  text_content: string;
  character_count: number;
  word_count: number;
  status: 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// --- Meeting Analysis ---
export interface AnalysisResponse {
  id: string;
  source_id: string | null;
  source_type: 'transcription' | 'document' | 'direct_text' | 'pasted_text';
  title: string | null;
  executive_summary: string;
  meeting_purpose: string;
  key_discussion_points: string[];
  decisions_made: string[];
  risks_and_blockers: string[];
  unresolved_questions: string[];
  topics_and_themes: string[];
  llm_provider: string;
  llm_model: string;
  status: 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// --- Tasks ---
export interface TaskResponse {
  id: string;
  analysis_id: string;
  description: string;
  assignee: string | null;
  has_missing_assignee: boolean;
  due_date: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  dependencies: string[];
  evidence_excerpt: string | null;
  created_at: string;
  updated_at: string;
}

// --- Follow-up Plan ---
export interface FollowUpPlanResponse {
  analysis_id: string;
  immediate_actions: TaskResponse[];
  upcoming_tasks: TaskResponse[];
  clarification_needed: TaskResponse[];
  blockers_and_dependencies: TaskResponse[];
  pending_decisions: string[];
  ai_suggestions: string[];
  total_tasks: number;
  generated_at: string;
}

// --- LangGraph Workflow Consolidated Result ---
export interface WorkflowResultResponse {
  id: string;
  source_type: string;
  source_id: string | null;
  title: string | null;
  current_stage: WorkflowStage;
  status: WorkflowStatus;
  analysis: AnalysisResponse | null;
  tasks: TaskResponse[];
  follow_up_plan: FollowUpPlanResponse | null;
  error_stage: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}
```

---

## 4. Polling Pattern for Asynchronous Workflows

When using the asynchronous workflow start (`POST /api/workflows/start`) or recorded audio transcription:

```typescript
// Helper polling utility for asynchronous LangGraph workflow progress
export async function pollWorkflowUntilComplete(
  workflowId: string,
  onProgress?: (stage: string, status: string) => void,
  intervalMs = 2000,
  maxAttempts = 60
): Promise<WorkflowResultResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const statusResp = await fetch(`http://127.0.0.1:8000/api/workflows/${workflowId}`);
    if (!statusResp.ok) {
      throw new Error(`Failed to fetch workflow status: ${statusResp.statusText}`);
    }
    const statusData = await statusResp.json();

    if (onProgress) {
      onProgress(statusData.current_stage, statusData.status);
    }

    if (statusData.status === 'completed') {
      const resultResp = await fetch(`http://127.0.0.1:8000/api/workflows/${workflowId}/result`);
      return (await resultResp.json()) as WorkflowResultResponse;
    }

    if (statusData.status === 'failed') {
      throw new Error(
        `Workflow failed at stage '${statusData.error_stage}': ${statusData.error_message}`
      );
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error('Workflow timed out waiting for completion.');
}
```

---

## 5. UI Component Integration Blueprints

### 5.1 One-Click Synchronous Meeting Analysis
For rapid direct text or document processing, use `POST /api/workflows/run-sync`:

```typescript
async function handleProcessMeeting(text: string, title?: string) {
  const response = await fetch('http://127.0.0.1:8000/api/workflows/run-sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_type: 'direct_text',
      source_id: null,
      text: text,
      title: title || 'Meeting Analysis',
      force_reanalyze: false,
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Meeting processing failed');
  }

  const result: WorkflowResultResponse = await response.json();
  return result; // Contains analysis, tasks, and follow_up_plan ready for rendering
}
```

### 5.2 Interactive Task Status Toggle
To toggle task execution between `pending` and `completed`:

```typescript
async function toggleTaskStatus(taskId: string, currentStatus: TaskStatus) {
  const newStatus: TaskStatus = currentStatus === 'completed' ? 'pending' : 'completed';
  const response = await fetch(`http://127.0.0.1:8000/api/tasks/${taskId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus }),
  });
  return (await response.json()) as TaskResponse;
}
```

### 5.3 Export File Download Handler
To download meeting deliverables as JSON, CSV, or Markdown:

```typescript
function downloadExport(format: 'json' | 'csv' | 'markdown', analysisId?: string) {
  const params = new URLSearchParams({ format });
  if (analysisId) {
    params.append('analysis_id', analysisId);
  }
  const url = `http://127.0.0.1:8000/api/tasks/export?${params.toString()}`;
  
  // Trigger native browser file download
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `meeting_export.${format === 'markdown' ? 'md' : format}`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

---

## 6. Nullability & Safety Guidelines

1. **`has_missing_assignee`**: When `true`, `assignee` is `null`. Render an "*(Unassigned)*" warning pill with an action button to assign an owner.
2. **`due_date`**: May be `null` if no explicit deadline was stated in the meeting. Render an "Add deadline" input.
3. **`evidence_excerpt`**: May be `null` for manually created tasks. When present, render as a tooltip or collapsible quote for transparency.
4. **`source_id` in Workflows**: Must be `null` when `source_type === "direct_text"`. Must be a valid string ID when `source_type === "transcription"` or `source_type === "document"`.
5. **Error Handling**:
   - `400 Bad Request` $\to$ Display validation message in form.
   - `413 Content Too Large` $\to$ Prompt user to upload audio under 100MB.
   - `422 Unprocessable Content` $\to$ Prompt user to upload a text-based document (not a scanned image PDF).
   - `502 Bad Gateway` / `503 Service Unavailable` $\to$ Inform user that the LLM or Database service is temporarily unavailable.
