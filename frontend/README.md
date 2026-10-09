# MeetMind — AI Business Meeting Assistant

> **Turn every meeting into clear decisions, accountable actions, and meaningful follow-through.**

MeetMind is an executive-grade AI web application that converts recorded business meeting audio into structured, actionable outcomes. Powered by local **OpenAI Whisper** transcription, **Groq Llama-3.3-70b** inference, and **LangGraph** multi-agent reasoning, it eliminates missed agreements and automates post-meeting follow-through.

---

## 🚀 Key Features

1. **Audio Recording Uploader & Local Whisper Pipeline**:
   - Drag-and-drop uploader supporting MP3, WAV, M4A, FLAC, OGG, WebM up to 250 MB.
   - Local on-premises Whisper transcription with auto-language detection and model tier selection.
   - Explicit zero-data-retention (ZDR) privacy design.

2. **Full-Featured Transcript Workspace**:
   - Plain-text editing with save/discard state management and unsaved changes warnings.
   - In-transcript search with instant match highlighting.
   - Timestamped speaker segment browser and navigation.
   - One-click copy and plain-text export (.txt).

3. **AI Meeting Insights & Multi-Agent Reasoning**:
   - Executive Briefing & Primary Purpose synthesis via LangGraph.
   - Structured key discussion points and thematic topic tagging.
   - Risk & Blocker detection, open questions, and tactical next steps.
   - Model traceability attribution (`Groq Llama-3.3-70b-versatile via LangGraph`).

4. **Decisions Management**:
   - Formal extraction of leadership agreements with supporting transcript quotes.
   - Status lifecycle tracking (`Proposed`, `Confirmed`, `Rejected`, `Superseded`).
   - Categorization by domain (Architecture, Strategy, Hiring, etc.).
   - Full manual CRUD support and CSV export.

5. **Action Items & Accountability Kanban**:
   - Dual List and Board (Kanban) execution interfaces.
   - Assignee attribution, email notifications, priorities (`Urgent`, `High`, `Medium`, `Low`), and overdue detection.
   - Single-click status changes across `To Do`, `In Progress`, `Blocked`, and `Completed`.

6. **Follow-up Execution Plans**:
   - Ordered milestone timeline with target timing, owners, and progress percentage.
   - Key target outcomes checklist and scheduled check-in sync dates.
   - Automatic generation from meeting outcomes or manual custom plans.

7. **Reports & Exports**:
   - **PDF Document**: Executive formatted printable brief with letterhead banner.
   - **Markdown (.md)**: Clean documentation ready for Notion / GitHub / Linear.
   - **CSV**: Tabular export for spreadsheets (Decisions & Action Items).
   - **JSON**: Complete structured data schema for programmatic consumption.
   - **TXT**: Plain transcript downloads.

8. **Dual Mode Architecture (Demo & Live FastAPI)**:
   - **Demo Mode**: Instant out-of-the-box experience with preloaded executive datasets, simulated Whisper transcription, and LangGraph analysis.
   - **Live FastAPI Mode**: Direct connection to your Python FastAPI backend at `http://localhost:8000`.

9. **Design System & Accessibility**:
   - Desktop-first SaaS shell with collapsible sidebar, mobile drawer, and header breadcrumbs.
   - Light and Dark mode with persistence.
   - Global keyboard search modal (`Cmd+K` / `Ctrl+K`).
   - Activity notifications center.

---

## 🛠️ Technology Stack

- **Framework**: React 18 + Vite + TypeScript
- **Styling**: Tailwind CSS + Custom MeetMind Design Tokens
- **Icons**: Lucide React
- **Charts**: Recharts (Velocity timeline, task status donuts)
- **Data Fetching & Cache**: TanStack Query (React Query) + Centralized Axios client
- **PDF Generation**: jsPDF
- **Notifications**: Sonner

---

## 📦 Getting Started

### Prerequisites

- Node.js v18+ (tested on v22)
- npm v9+

### Installation

```bash
# Clone or navigate to the project directory
cd meetmind

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will launch at `http://localhost:3000`.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Available variables:

```env
# Base URL for the FastAPI backend service
VITE_API_BASE_URL=http://localhost:8000

# Enable/Disable default demo mode fallback
VITE_ENABLE_DEMO_FALLBACK=true
```

---

## 🔗 Connecting to the FastAPI Backend

MeetMind includes a service layer in `src/services/` pre-configured to communicate with the FastAPI backend contracts:

- **Health**: `GET /api/health`
- **Meetings**: `GET/POST /api/meetings`, `GET/PATCH/DELETE /api/meetings/{id}`
- **Transcription**: `POST /api/transcriptions`, `GET/PATCH/DELETE /api/transcriptions/{id}`
- **AI Analysis**: `POST /api/meetings/{id}/analyze`, `GET /api/meetings/{id}/analysis`
- **Decisions**: `GET/POST /api/decisions`, `PATCH/DELETE /api/decisions/{id}`
- **Action Items**: `GET/POST /api/action-items`, `PATCH/DELETE /api/action-items/{id}`
- **Follow-up Plans**: `GET/POST /api/meetings/{id}/follow-up`, `PATCH/DELETE /api/follow-ups/{id}`

To switch between **Demo Mode** and **Live FastAPI Mode**, click the status pill in the top header or toggle the option under **Settings > Backend Server**.
