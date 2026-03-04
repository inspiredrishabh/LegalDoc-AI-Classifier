# LegalDoc AI Classifier


A **fully offline** legal document analysis platform. Upload legal documents (PDF, JPG, PNG), extract text via PaddleOCR, and ask natural-language questions answered by a local LLM grounded in Indian legal acts.

No cloud APIs required — OCR runs locally with PaddleOCR and the LLM runs via Ollama.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
  - [Backend](#backend-setup)
  - [Frontend](#frontend-setup)
  - [Ollama (LLM)](#ollama-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Data Pipeline Flow](#data-pipeline-flow)
- [Legal Datasets](#legal-datasets)
- [Testing](#testing)

---

## Features

| Capability          | Description                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| **Offline OCR**     | PaddleOCR extracts text from PDFs and images — supports English and Hindi      |
| **Legal Q&A**       | Ask questions about Indian law; answers are sourced from act datasets + LLM    |
| **Document Upload** | Batch upload with background processing, progress tracking, and result polling |
| **Local LLM**       | Ollama + Mistral (or any compatible model) — no API keys needed                |
| **Review Mode**     | View extracted text alongside the original document in the browser             |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                 │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────────────────────┐   │
│  │  Upload  │   │  Review  │   │    Ask Legal Question  │   │
│  │  Tab     │   │  Tab     │   │    Tab                 │   │
│  └────┬─────┘   └────┬─────┘   └────────┬───────────────┘   │
│       │              │                  │                   │
│       └──────────────┴──────────────────┘                   │
│                        │  Axios (HTTP)                      │
└────────────────────────┼────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI, Python 3.12+)            │
│                                                             │
│  Routes:                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ GET  /health              → Health check             │   │
│  │ POST /v1/ask              → Legal question pipeline  │   │
│  │ POST /v1/files/upload-batch → Batch document upload  │   │
│  │ GET  /v1/files/batch/{id} → Poll processing status   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Services:                                                  │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │ VisionSvc  │  │ QAService  │  │ PipelineService       │  │
│  │ (PaddleOCR)│  │ (Jaccard)  │  │ (6-step orchestrator) │  │
│  └────────────┘  └────────────┘  └───────────────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐  │
│  │RetrievalSv │  │ ContextSvc │  │ LLM Service (Ollama)  │  │
│  │ (keyword)  │  │ (builder)  │  │                       │  │
│  └────────────┘  └────────────┘  └───────────────────────┘  │
│                                                             │
│  Data: data/acts/*.json  +  data/qa/*.json                  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Ollama (local LLM)  │
              │  mistral / llama3    │
              └──────────────────────┘
```

---

## Tech Stack

### Backend

- **Python 3.12+**
- **FastAPI** — async web framework
- **PaddleOCR + PaddlePaddle** — offline OCR engine (English + Hindi)
- **pypdfium2** — PDF-to-image rendering (no system deps)
- **OpenCV** — image preprocessing (denoise, CLAHE, adaptive threshold)
- **Ollama** — local LLM inference (Mistral by default)
- **Pydantic v2** — settings and schema validation

### Frontend

- **React 18** + **TypeScript**
- **Vite** — build tool
- **TailwindCSS** — styling
- **TanStack React Query** — server state management
- **Zustand** — client state store
- **Axios** — HTTP client
- **react-dropzone** — file upload UX

---

## Project Structure

```
legaldoc-ai/
├── README.md
│
├── backend/
│   ├── pyproject.toml              # Project metadata, pytest config
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variable template
│   │
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory + lifespan
│   │   ├── config.py               # Pydantic Settings (env vars)
│   │   ├── dependencies.py         # Singleton service wiring (DI)
│   │   │
│   │   ├── routes/
│   │   │   ├── router.py           # Aggregates all route modules
│   │   │   ├── health.py           # GET /health
│   │   │   ├── ask.py              # POST /v1/ask
│   │   │   └── upload.py           # POST /v1/files/upload-batch + polling
│   │   │
│   │   ├── services/
│   │   │   ├── vision_service.py   # PaddleOCR engine (offline OCR)
│   │   │   ├── qa_service.py       # QA dataset lookup (Jaccard similarity)
│   │   │   ├── retrieval_service.py# Keyword-based act/section retrieval
│   │   │   ├── context_service.py  # Build LLM context from ranked sections
│   │   │   ├── prompt_service.py   # Construct LLM prompt
│   │   │   ├── llm_service.py      # Ollama REST client (Mistral)
│   │   │   ├── pipeline_service.py # 6-step Q&A orchestrator
│   │   │   └── preprocessing.py    # (legacy, unused — kept for reference)
│   │   │
│   │   ├── models/
│   │   │   ├── enums.py            # ProcessingStatus, AnswerMethod enums
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   │
│   │   ├── loaders/
│   │   │   └── data_loader.py      # Load acts + QA JSON datasets at startup
│   │   │
│   │   └── utils/
│   │       ├── file_validation.py  # MIME type validation (python-magic)
│   │       ├── text_processing.py  # Normalize text, Jaccard similarity
│   │       └── retry.py            # Async retry with exponential backoff
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_upload_endpoint.py
│       ├── test_pipeline_service.py
│       ├── test_qa_service.py
│       ├── test_retrieval_service.py
│       ├── test_context_service.py
│       └── test_data_loader.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   │
│   └── src/
│       ├── main.tsx                # React entry point
│       ├── App.tsx                 # Tab layout (Upload / Review / Ask)
│       ├── index.css               # Tailwind imports
│       │
│       ├── api/
│       │   ├── axios-instance.ts   # Axios client (baseURL, interceptors)
│       │   ├── upload-api.ts       # uploadBatch(), pollBatchStatus()
│       │   └── ask-api.ts          # askLegal()
│       │
│       ├── components/
│       │   ├── layout/             # Header, Layout shell
│       │   ├── upload/             # MultiFileUpload, FilePreview, Progress
│       │   ├── review/             # ExtractedText, OriginalView, ReviewMode
│       │   ├── ask/                # QueryInput, AnswerDisplay
│       │   └── common/             # ErrorBoundary, LoadingSpinner
│       │
│       ├── hooks/
│       │   ├── useAskLegal.ts      # React Query mutation for /v1/ask
│       │   └── useDocumentProcessor.ts  # Upload + polling logic
│       │
│       ├── stores/
│       │   └── document-store.ts   # Zustand store for uploaded docs
│       │
│       ├── types/
│       │   └── index.ts            # TypeScript interfaces
│       │
│       └── utils/
│           └── format.ts           # Formatting helpers
│
└── data/
    ├── acts/                       # Indian legal act datasets (JSON)
    │   ├── cpc.json                # Code of Civil Procedure
    │   ├── crpc.json               # Code of Criminal Procedure
    │   ├── hma.json                # Hindu Marriage Act
    │   ├── ida.json                # Indian Divorce Act
    │   ├── iea.json                # Indian Evidence Act
    │   ├── ipc.json                # Indian Penal Code
    │   ├── mva.json                # Motor Vehicles Act
    │   └── nia.json                # Negotiable Instruments Act
    │
    └── qa/                         # Pre-built Q&A pairs (JSON)
        ├── constitution_qa.json
        ├── crpc_qa.json
        └── ipc_qa.json
```

---

## Prerequisites

| Dependency  | Version | Purpose                  |
| ----------- | ------- | ------------------------ |
| **Python**  | 3.12+   | Backend runtime          |
| **Node.js** | 18+     | Frontend build toolchain |
| **Ollama**  | latest  | Local LLM inference      |

> **Note:** No cloud accounts, API keys, or external services are required. Everything runs locally.

---

## Setup & Installation

### Backend Setup

```bash
cd backend

# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

> **Windows permission error?** If you get `WinError 5: Access is denied` during install (typically opencv conflicting with a system-wide install), use `pip install --user -r requirements.txt` or install inside a fresh virtual environment.

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# That's it — Vite handles the rest
```

### Ollama Setup

Ollama provides the local LLM that powers the "Ask Legal" feature.

```bash
# 1. Install Ollama from https://ollama.com

# 2. Pull the Mistral model (default)
ollama pull mistral

# 3. Ollama runs as a background service on http://localhost:11434
#    Verify with:
curl http://localhost:11434/api/tags
```

You can use a different model by changing `OLLAMA_MODEL` in your `.env` file.

---

## Configuration

All backend configuration is via environment variables (loaded from `backend/.env`):

| Variable           | Default                  | Description                                           |
| ------------------ | ------------------------ | ----------------------------------------------------- |
| `PORT`             | `8000`                   | Backend server port                                   |
| `DEBUG`            | `false`                  | Debug mode                                            |
| `ALLOWED_ORIGINS`  | `http://localhost:5173`  | CORS origins (comma-separated)                        |
| `OCR_LANG`         | `auto`                   | OCR language: `auto` (English + Hindi), `en`, or `hi` |
| `LLM_MODE`         | `local`                  | LLM provider mode                                     |
| `OLLAMA_HOST`      | `http://localhost:11434` | Ollama server URL                                     |
| `OLLAMA_MODEL`     | `mistral`                | Ollama model name                                     |
| `MAX_FILE_SIZE_MB` | `50`                     | Max upload file size in MB                            |

Frontend API base URL is configured via `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

---

## Running the Application

### 1. Start Ollama (if not already running)

```bash
ollama serve
```

### 2. Start the Backend

```bash
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

uvicorn app.main:app --reload --port 8000
```

The backend loads all legal datasets on startup and initializes the OCR service. PaddleOCR models are downloaded on first use and cached locally.

- API docs: http://localhost:8000/docs (Swagger UI)
- Health: http://localhost:8000/health

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

---

## API Reference

### `GET /health`

Health check. Returns server and LLM status.

```json
{ "status": "ok", "service": "LegalDoc AI Backend", "llm_mode": "local" }
```

### `POST /v1/ask`

Ask a legal question. The 6-step pipeline:

1. Check QA dataset for a direct match (confidence ≥ 0.85 → instant return)
2. Retrieve relevant act sections via keyword matching
3. Build context from top-ranked sections
4. Verify LLM availability
5. Generate answer via Ollama
6. Return result

**Request:**

```json
{ "query": "What is the punishment for theft under IPC?" }
```

**Response:**

```json
{
  "answer": "Under Section 379 of the IPC...",
  "source": "LLM + Legal Acts",
  "method": "llm",
  "confidence": null
}
```

### `POST /v1/files/upload-batch`

Upload one or more documents (PDF, JPG, PNG) for OCR extraction.

**Request:** `multipart/form-data` with field `files` (multiple).

**Response:**

```json
{
  "batch_id": "uuid-...",
  "results": [
    {
      "file_id": "uuid-...",
      "status": "pending",
      "raw_text": "",
      "metadata": { "page_count": 0, "confidence_score": 0.0 },
      "error": null
    }
  ]
}
```

Files are processed in the background. Poll status with:

### `GET /v1/files/batch/{batch_id}`

Returns the same shape as the upload response, with updated statuses (`processing`, `completed`, or `failed`).

---

## Data Pipeline Flow

### Document Upload Flow

```
User drops files ──► Frontend (react-dropzone)
                         │
                         ▼
                    POST /v1/files/upload-batch
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Validate    Validate    Validate
         (size,      (size,      (size,
          MIME)       MIME)       MIME)
              │          │          │
              ▼          ▼          ▼
         Background  Background  Background
         Task        Task        Task
              │          │          │
              ▼          ▼          ▼
         ┌─────────────────────────────┐
         │      VisionService          │
         │  (PaddleOCR, offline)       │
         │                             │
         │  PDF → pypdfium2 → images   │
         │  Image → cv2 decode         │
         │         │                   │
         │         ▼                   │
         │  Preprocess (grayscale,     │
         │   denoise, CLAHE, thresh)   │
         │         │                   │
         │         ▼                   │
         │  PaddleOCR (en/hi/auto)     │
         │         │                   │
         │         ▼                   │
         │  Sort reading order         │
         │         │                   │
         │         ▼                   │
         │  { raw_text, page_count,    │
         │    confidence_score }       │
         └─────────────────────────────┘
              │
              ▼
         Status → completed / failed
         Frontend polls GET /v1/files/batch/{id}
```

### Legal Q&A Flow (6-Step Pipeline)

```
User types question ──► POST /v1/ask
                              │
                    ┌─────────┴─────────┐
                    ▼                   │
            Step 1: QA Dataset          │
            (Jaccard similarity)        │
            confidence ≥ 0.85? ──Yes──► Return direct match
                    │ No                │
                    ▼                   │
            Step 2: Retrieve Sections   │
            - Analyze query tokens      │
            - Detect acts (IPC, CRPC…)  │
            - Extract section numbers   │
            - Keyword-rank sections     │
                    │                   │
                    ▼                   │
            Step 3: Build Context       │
            (top sections, max 3000ch)  │
                    │                   │
                    ▼                   │
            Step 4: Check LLM           │
            (Ollama /api/tags)          │
                    │                   │
                    ▼                   │
            Step 5: Generate Answer     │
            (Ollama + Mistral)          │
                    │                   │
                    ▼                   │
            Step 6: Return              │
            { answer, source, method }  │
                    └───────────────────┘
```

---

## Legal Datasets

The `data/` directory contains pre-structured Indian legal act data and Q&A pairs:

### Acts (`data/acts/`)

| File        | Act                        | Description                       |
| ----------- | -------------------------- | --------------------------------- |
| `ipc.json`  | Indian Penal Code          | Criminal offences and punishments |
| `crpc.json` | Code of Criminal Procedure | Criminal court procedures         |
| `cpc.json`  | Code of Civil Procedure    | Civil court procedures            |
| `iea.json`  | Indian Evidence Act        | Rules of evidence                 |
| `hma.json`  | Hindu Marriage Act         | Marriage and divorce law          |
| `ida.json`  | Indian Divorce Act         | Divorce proceedings               |
| `mva.json`  | Motor Vehicles Act         | Vehicle regulations               |
| `nia.json`  | Negotiable Instruments Act | Cheque dishonour, etc.            |

Each JSON file contains an array of sections with fields like `section`, `title`/`section_title`, and `description`/`section_desc`.

### QA Pairs (`data/qa/`)

Pre-built question-answer pairs for fast lookup without LLM. Used as Step 1 in the pipeline for instant responses when confidence is high (≥ 0.85).

---

## Testing

```bash
cd backend
venv\Scripts\activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_upload_endpoint.py
```

Tests mock external services (Vision, LLM) so they run without PaddleOCR or Ollama installed.

---

## Troubleshooting

| Issue                                             | Solution                                                                                                      |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `WinError 5: Access is denied` during pip install | Use a virtual environment (`python -m venv venv`) or add `--user` flag                                        |
| PaddleOCR model download fails                    | First run requires internet to download models (~100 MB). After that, everything is cached and works offline. |
| Ollama connection refused                         | Make sure Ollama is running: `ollama serve`                                                                   |
| OCR returns empty text                            | Try setting `OCR_LANG=en` or `OCR_LANG=hi` in `.env` instead of `auto`                                        |
| Frontend can't reach backend                      | Check `ALLOWED_ORIGINS` includes `http://localhost:5173` and backend is on port 8000                          |

---

## License

This project is for educational and research purposes.
