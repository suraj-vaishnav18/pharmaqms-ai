# PharmaQMS AI — AI-Powered Quality Complaint Management System

An AI-native complaint intake and triage system for pharmaceutical
manufacturing quality assurance teams. Built to explore how an agentic
LLM pipeline (LangGraph) can assist — not replace — human QA analysts
in a regulated, human-in-the-loop workflow.

## What it does

- **AI Intake Copilot** — paste raw complaint text (email, verbal report) or
  drop a PDF, and the AI extracts structured fields (product, batch,
  manufacturing/expiry dates, affected quantity, severity, suggested next
  action, risk assessment) and populates the intake form live. Any field can
  be corrected conversationally (*"actually the batch number is X and
  quantity is 48 capsules"*) — only the mentioned fields update, everything
  else is preserved.
- **LangGraph triage pipeline** — once a complaint is logged, an AI pipeline
  chains together completeness checking, duplicate detection (TF-IDF cosine
  similarity), severity/category classification, root cause hypothesis
  generation, CAPA (Corrective and Preventive Action) recommendation, and an
  executive summary — with conditional branching (duplicates skip straight
  to summary, no wasted LLM calls).
- **CAPA tracking** — AI-suggested corrective/preventive actions are
  surfaced as suggestions, not auto-created. A QA analyst reviews and clicks
  "Track as CAPA" to promote one into a real tracked action item — a
  deliberate human-in-the-loop design choice mirroring real QMS software.
- **Full audit trail** — every AI pipeline run is logged with a step-by-step
  trace (what ran, in what order, with what result), viewable in the UI as
  a "Pipeline Trace" panel — useful for explaining *why* the AI reached a
  conclusion, which matters in a regulated domain.

## Architecture

- **Backend**: FastAPI + SQLAlchemy (SQLite by default, Postgres-ready) +
  LangGraph agent pipeline
- **Frontend**: React + Redux Toolkit + Vite
- **AI**: Groq-hosted models — a fast model for classification/extraction,
  a larger reasoning model for root-cause/CAPA generation

### LangGraph pipeline (`backend/app/agents/graph.py`)

```
completeness_check -> duplicate_check -+-> [is duplicate] -> summary
                                        +-> classification -> root_cause -> capa_recommendation -> summary
```

Every step appends to a `trace` list in the pipeline state, persisted to
`audit_log` and exposed via `GET /complaints/{id}/ai-trace`.

### AI Intake Copilot (`backend/app/agents/copilot.py`, `backend/app/routers/copilot.py`)

- `POST /copilot/extract-text` — extracts structured fields from pasted text
- `POST /copilot/extract-file` — same, from an uploaded PDF (via `pypdf`)
- `POST /copilot/chat` — applies a natural-language correction to
  already-extracted fields, merging only what changed without dropping
  previously extracted data

## Setup

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env          # then fill in GROQ_API_KEY
uvicorn app.main:app --reload
```
Runs at http://localhost:8000 (interactive docs at `/docs`). Uses a local
SQLite file by default — no separate database install needed. Get a free
Groq API key at https://console.groq.com

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173

## Project structure

```
backend/
  app/
    agents/
      graph.py       # LangGraph pipeline definition
      nodes.py        # individual pipeline node functions
      copilot.py       # intake extraction / chat correction logic
      llm.py             # LLM client wrapper (fast vs. reasoning model)
    routers/
      complaints.py      # complaint CRUD + run-ai-pipeline endpoint
      capa.py              # CAPA action CRUD
      copilot.py             # AI intake copilot endpoints
    models.py                  # SQLAlchemy models
    schemas.py                   # Pydantic request/response schemas
    main.py                        # FastAPI app entrypoint
frontend/
  src/
    pages/
      AiIntakePage.jsx            # chat-driven intake copilot UI
      ComplaintListPage.jsx        # complaint dashboard
      ComplaintDetailPage.jsx        # detail view, AI pipeline trigger, CAPA UI
    store/                              # Redux Toolkit slices
    api/client.js                          # backend API client
```

## Design decisions

- **CAPA creation is human-triggered, not automatic.** The AI recommends
  corrective/preventive actions; a QA analyst clicks "Track as CAPA" to
  promote a suggestion into a tracked action item. AI recommends, human
  approves — never the reverse, especially in a regulated domain.
- **Duplicate detection uses TF-IDF cosine similarity**, not embeddings.
  Rare/distinctive words are weighted higher than common ones (e.g.
  "tablet" vs. "discoloration"), giving meaningfully better results than
  raw keyword overlap without pulling in a heavier embeddings model/vector
  DB than this scope needs.
- **Two-tier model usage**: a fast, cheap model handles routine
  classification/extraction; a larger reasoning model is reserved for
  root-cause and CAPA generation, where more context and reasoning depth
  actually pay off.
- **SQLite by default** for zero-setup local development; swap
  `DATABASE_URL` in `.env` for a Postgres connection string when needed — no
  code changes required, since models use portable column types.

## Possible extensions

- Real embedding-based duplicate detection (e.g. `pgvector`) for larger
  complaint volumes
- Auth / role-based access so the audit trail reflects real users
- Risk Classification as its own dedicated pipeline node (currently derived
  from severity)
- Email/EML parsing in addition to PDF for the intake copilot
