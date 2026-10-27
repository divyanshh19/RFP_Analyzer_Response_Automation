# AI-Powered RFP Intelligence & Response Automation Platform

An enterprise platform designed to ingest complex Request for Proposal (RFP) documents, extract requirements into structured compliance matrices, and use grounded Retrieval-Augmented Generation (RAG) to draft compliant responses based on an organization's verified knowledge base.

---

## 🚀 Key Features

- **Document Ingestion & Parsing**: Parses PDF and DOCX files with OCR fallback for scanned tender documents.
- **Automated Requirement Extraction**: Uses Google Gemini 3.5 Flash to automatically detect, classify, and extract line-item requirements (IDs, categories, mandatory status, priorities).
- **Grounded RAG Pipeline**:
  - Uses local ONNX embeddings (`sentence-transformers/all-MiniLM-L6-v2`) to eliminate API rate limits and latency.
  - Queries persistent ChromaDB vector store.
  - Enforces strict anti-hallucination guardrails: if evidence is not found in the uploaded knowledge base, the system responds with *"Insufficient evidence in the knowledge base"* instead of fabricating details.
- **Response Review & Editing**: Interactive compliance matrix UI for reviewing, auto-answering, and manually revising proposed responses.
- **Audit & Export**: Exports final compliance responses and tables into Microsoft Word (`.docx`).

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, Axios
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, Pydantic v2
- **Relational DB**: MySQL
- **Vector DB**: ChromaDB
- **Embeddings**: `all-MiniLM-L6-v2` (Local ONNX)
- **AI/LLM Provider**: Google Gemini (`gemini-3.5-flash` via `google-genai` SDK)

---

## 📂 Project Structure

```
AI_RFP_Analyzer/
└── rfp-ai-platform/
    ├── backend/
    │   ├── app/
    │   │   ├── api/routers/        # API endpoints (auth, rfp, generation, export)
    │   │   ├── core/               # Configuration & JWT security
    │   │   ├── db/                 # Database engine & session
    │   │   ├── models/             # SQLAlchemy ORM models
    │   │   ├── repositories/       # Database access layers
    │   │   ├── schemas/            # Pydantic models
    │   │   └── services/           # Extraction, Ingestion, ChromaDB, RAG, Export
    │   ├── alembic.ini
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── components/         # Upload, Matrix, Review components
    │   │   ├── pages/              # App views (Dashboard, Project Detail)
    │   │   └── api/                # API client configuration
    │   ├── package.json
    │   └── vite.config.js
    ├── docker-compose.yml          # Container configuration for MySQL & Chroma
    └── .env.example                # Template for environment variables
```

---

## ⚙️ Getting Started

### 1. Environment Setup
Copy `.env.example` in `rfp-ai-platform/` to `.env` and fill in your credentials:
```bash
cp rfp-ai-platform/.env.example rfp-ai-platform/.env
```

### 2. Backend Setup
```bash
cd rfp-ai-platform/backend
python -m venv venv
.\venv\Scripts\activate   # On Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd rfp-ai-platform/frontend
npm install
npm run dev
```

---

## 📄 License
MIT License
