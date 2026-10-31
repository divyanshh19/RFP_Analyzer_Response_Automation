# Autonomous RFP Analyzer & Response Automation Platform
### Enterprise Full-Stack Agentic AI Platform powered by LangGraph, Model Context Protocol (MCP), Java 21 Spring Boot, Python FastAPI, and React

---

## 🌟 Executive Overview

The **Autonomous RFP Analyzer & Response Automation Platform** transforms how enterprises review, assess, and bid on complex Requests for Proposals (RFPs), tenders, and public procurement solicitations. 

By combining an enterprise-grade **Java 21 Spring Boot** application service, a high-performance **Python 3.11 FastAPI** AI microservice, a cyclical **LangGraph 9-Agent Orchestration Workflow**, and a standardized **Model Context Protocol (MCP)** tool ecosystem, the platform automates the entire proposal lifecycle while guaranteeing strict evidence grounding and eliminating AI hallucination.

```
       ┌────────────────────────────────────────────────────────┐
       │             React 19 Modern SaaS Frontend             │
       │  (Agentic Workflow Tracker, Compliance Matrix, Copilot)│
       └───────────────────────────┬────────────────────────────┘
                                   │ HTTP / JSON
       ┌───────────────────────────▼────────────────────────────┐
       │         Enterprise Java 21 / Spring Boot 3.3           │
       │   (REST API, Authentication, Workflow Client, MySQL)   │
       └───────────────────────────┬────────────────────────────┘
                                   │ RestClient (HTTP / JSON)
       ┌───────────────────────────▼────────────────────────────┐
       │             Python 3.11 FastAPI AI Service             │
       │  (LangGraph Orchestrator, FastMCP Adapters, RAG Engine) │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
       ┌──────────────▼────────────┐  ┌──────────▼──────────────┐
       │  LangGraph 9-Agent Graph  │  │  Custom FastMCP Servers │
       │  - MemorySaver Checkpoint │  │  - RFP Document Server  │
       │  - Human-in-the-Loop      │  │  - Knowledge Base Server│
       │  - Cyclical Re-Retrieval  │  │  - Compliance Server    │
       │  - Self-Correcting Revis. │  │  - Proposal Server      │
       └──────────────┬────────────┘  └──────────┬──────────────┘
                      │                          │
       ┌──────────────▼──────────────────────────▼──────────────┐
       │               Grounded Storage & Engine                │
       │   ChromaDB (ONNX all-MiniLM-L6-v2) | Google Gemini 3.5 │
       └────────────────────────────────────────────────────────┘
```

---

## 🏗️ System Architecture & Technology Stack

| Layer | Technologies & Frameworks | Description |
| :--- | :--- | :--- |
| **Frontend UI** | **React 19**, Vite, Tailwind CSS 4, Lucide Icons, Axios | Dynamic, responsive SPA featuring real-time 9-stage agent workflow tracker, evidence inspector modals, interactive compliance matrix, multi-section proposal editor, and floating AI Copilot drawer. |
| **Enterprise Backend** | **Java 21**, **Spring Boot 3.3.4**, Spring Data JPA, Hibernate, MySQL Driver | Enterprise application gateway managing user authentication, project lifecycle, document metadata, audit logs, and forwarding workflow tasks to the AI microservice via Spring `RestClient`. |
| **AI Agent Service** | **Python 3.11**, **FastAPI**, Pydantic v2, Google GenAI SDK | Microservice hosting the LangGraph agent state machine, FastMCP server registries, and local neural embedding pipelines. |
| **Orchestration** | **LangGraph 1.2+**, **LangChain 1.4+**, `langgraph-checkpoint` | Stateful 9-node computational graph with conditional self-correction loops, cyclical re-retrieval, and genuine `interrupt_before` human review checkpoints. |
| **Tool Protocol** | **Model Context Protocol (FastMCP 1.30+)**, `langchain-mcp-adapters` | Standardized tool abstraction decoupling agent reasoning from core business logic across 22 domain-specific tools. |
| **Grounded RAG** | **ChromaDB 0.4.24**, `sentence-transformers/all-MiniLM-L6-v2` | Persistent vector database powered by local ONNX embeddings with cosine similarity distance, zero API rate limits, and sub-second retrieval. |
| **Document Processing**| **PyMuPDF (fitz)**, **python-docx**, **Tesseract OCR (pytesseract)** | High-fidelity extraction pipeline with automatic scanned-document heuristic detection and OCR fallback. |

---

## 🤖 The 9-Agent LangGraph Workflow Lifecycle

The core intelligence engine operates as a stateful, cyclical multi-agent graph managed by `app.services.agent.graph.py`.

```mermaid
flowchart TD
    START([Start RFP Workflow]) --> Ingestion["1. Document Ingestion Agent"]
    Ingestion --> Analysis["2. Requirement Analysis Agent"]
    Analysis --> Retrieval["3. Knowledge Retrieval Agent"]
    Retrieval --> Compliance["4. Compliance Analysis Agent"]
    Compliance --> GapAnalysis{"5. Gap Analysis Agent"}
    
    %% Cyclical Re-Retrieval Loop
    GapAnalysis -- "Gaps Found & Retries < Max" --> Retrieval
    GapAnalysis -- "Satisfied / Retries Exhausted" --> Proposal["6. Proposal Generation Agent"]
    
    Proposal --> Validation{"7. Proposal Validation Agent"}
    
    %% Self-Correction Revision Loop
    Validation -- "Unsupported Claims / Incomplete" --> Proposal
    Validation -- "Verified Grounded" --> Interrupt(["8. Human Review Checkpoint\n(LangGraph Interrupt)"])
    
    %% Human-in-the-Loop Decision
    Interrupt -- "User: REVISE" --> Proposal
    Interrupt -- "User: APPROVED" --> Export["9. Proposal Export Agent"]
    Interrupt -- "User: REJECTED" --> Terminate([Workflow Terminated])
    
    Export --> Complete([Final Microsoft Word DOCX Ready])
```

### Detailed Agent Roles

1. **Document Ingestion Agent (`document_ingestion_node.py`)**:
   - Parses incoming PDF or DOCX files.
   - Evaluates text density to detect scanned documents; executes OCR fallback when digital text is insufficient.
2. **Requirement Analysis Agent (`requirements_node.py`)**:
   - Extracts discrete line-item requirements with categories, priorities, and mandatory flags.
   - Discovers submission deadlines, bidder eligibility criteria, scoring weightings, and mandatory submission attachments.
3. **Knowledge Retrieval Agent (`retrieval_node.py`)**:
   - Performs semantic vector search over ChromaDB for each requirement.
   - Augments queries with company capabilities, certifications (ISO, SOC 2, CMMI), and relevant case studies.
4. **Compliance Analysis Agent (`compliance_node.py`)**:
   - Compares requirements against retrieved evidence chunks.
   - Assigns one of four strict compliance statuses without hallucination.
   - Calculates overall compliance score and mandatory requirement compliance percentage.
5. **Gap Analysis Agent (`gap_analysis_node.py`)**:
   - Identifies non-compliant or clarification-required items.
   - Dynamically triggers a re-retrieval loop with expanded semantic query variations (up to configured retry limit).
6. **Proposal Generation Agent (`proposal_node.py`)**:
   - Drafts formal, evidence-backed narrative sections:
     - *Executive Summary & Solution Overview*
     - *Technical Architecture & Operational Approach*
     - *Security, Compliance & SLA Commitments*
     - *Implementation Roadmap & Team Qualifications*
   - Drafts line-item responses for the RFP compliance matrix.
7. **Proposal Validation Agent (`validation_node.py`)**:
   - Audits draft text against retrieved evidence chunks.
   - Flags unverified assertions and calculates traceability coverage score.
   - Triggers automated self-correction revision loop if unsupported claims are found.
8. **Human Review Agent (`human_review_node.py`)**:
   - LangGraph pauses execution using `interrupt_before=["human_review"]`.
   - Persists execution state in memory/database checkpointer.
   - Allows users to review the compliance matrix, read drafted sections, edit text, and choose `APPROVED`, `REVISE`, or `REJECTED`.
9. **Proposal Export Agent (`export_node.py`)**:
   - Compiles finalized proposal sections and the complete compliance matrix into a styled, professional Microsoft Word document (`.docx`).

---

## 🔌 Model Context Protocol (MCP) Hybrid Architecture

The platform adopts a hybrid Model Context Protocol (MCP) architecture. Rather than arbitrary tool sprawl, 4 domain-specific FastMCP servers provide 22 purpose-built tools:

### 1. RFP Document Server (`app/mcp/rfp_document_server.py`)
- `extract_rfp_text`: Digital & OCR text extraction from PDF/DOCX.
- `extract_rfp_requirements`: Line-item requirement extraction into structured Pydantic schemas.
- `extract_deadlines`: Identification of critical milestone dates, submission deadlines, and pre-bid conferences.
- `extract_eligibility_criteria`: Bidder eligibility conditions (revenue, experience, certifications).
- `extract_evaluation_criteria`: Scoring formulas, evaluation weightings, and technical review grids.
- `extract_mandatory_documents`: Discovers mandatory annexures, bid bonds, and declaration forms.

### 2. Knowledge Base Server (`app/mcp/knowledge_base_server.py`)
- `search_company_documents`: Vector similarity search across company whitepapers, past bids, and profiles.
- `search_previous_proposals`: Semantic lookup of previously awarded winning proposal responses.
- `retrieve_company_capabilities`: Specific capability statement lookups by technical domain.
- `retrieve_certifications`: Verification of security certifications (SOC 2, ISO 27001, HIPAA, FedRAMP).
- `retrieve_relevant_experience`: Industry case studies, project timelines, and past performance records.
- `search_supporting_evidence`: Targeted chunk retrieval directly mapped to RFP requirement text.

### 3. Compliance Server (`app/mcp/compliance_server.py`)
- `map_requirements_to_capabilities`: Grounded compliance assessment with strict anti-hallucination rules.
- `identify_missing_requirements`: Filters compliance matrix for gaps to drive targeted re-retrieval.
- `calculate_compliance_score`: Mathematical computation of aggregate compliance metrics.
- `validate_response_coverage`: Audits response completeness across all extracted requirements.
- `retrieve_requirement_evidence`: Gathers full citation records for audit transparency.

### 4. Proposal Server (`app/mcp/proposal_server.py`)
- `generate_proposal_section`: Drafts evidence-grounded proposal sections.
- `validate_proposal_content`: Fact-checks drafted sections against verified evidence chunks.
- `revise_proposal_section`: Refines section drafts using feedback or QA audit critique.
- `save_proposal_draft`: Persists working drafts to disk and database.
- `export_proposal`: Compiles complete bid package into styled Microsoft Word (.docx).

---

## 🎯 Grounded Compliance Matrix & Anti-Hallucination Guardrails

To meet strict procurement audit standards, the platform guarantees that **no compliance score or response claim is fabricated**:

### Four Strict Compliance Statuses
1. **`Compliant`**: Requirement is explicitly proven by uploaded knowledge base documents. Full citations provided.
2. **`Partially compliant`**: Company meets core aspects but lacks explicit evidence for sub-clauses.
3. **`Non-compliant`**: Explicitly contradicts company capabilities or zero matching evidence exists.
4. **`Requires clarification`**: Ambiguous RFP clause requiring customer Q&A submission or SME input.

### Compliance Score Calculation
$$\text{Overall Score} = \frac{\sum \text{Score}_i}{N} \times 100\% \quad (\text{Compliant} = 1.0, \text{Partial} = 0.5, \text{Clarification} = 0.5, \text{Non-Compliant} = 0.0)$$

$$\text{Mandatory Score} = \frac{\sum_{i \in \text{Mandatory}} \text{Score}_i}{M} \times 100\%$$

Each compliance item includes:
- **`requirement_id`** (e.g., `REQ-001`)
- **`status`** (one of the 4 strict statuses above)
- **`compliance_score`** ($0.0$ to $1.0$)
- **`rationale`** (concise explanation of why the score was assigned)
- **`evidence_citations`** (exact chunk IDs, document names, page numbers, and similarity metrics)
- **`missing_information`** (clear statement of what additional proof is needed)

---

## 💬 Enterprise AI Copilot

The embedded **AI Copilot** (`app.services.assistant.copilot_service.py`) provides real-time guidance through an interactive drawer:

- **Context-Aware Multi-Turn Chat**: Retains project session state, RFP requirements, compliance metrics, and draft sections.
- **Dynamic Tool Calling**: Uses `search_company_documents` to lookup facts on demand when answering user questions.
- **Evidence Citations**: Every answer includes clickable source citation chips `[Page X, Section Y]`.
- **Suggested Follow-up Prompts**: Automatically generates contextual follow-up questions to accelerate proposal work.

---

## 📡 REST API Reference

### Java 21 / Spring Boot API (`http://localhost:8080`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status. |
| `GET` | `/api/projects` | List all RFP workspaces. |
| `POST` | `/api/projects` | Create a new RFP workspace. |
| `GET` | `/api/projects/{id}` | Get workspace details and documents. |
| `POST` | `/api/projects/{id}/workflow/start` | Trigger 9-agent LangGraph workflow. |
| `GET` | `/api/projects/{id}/workflow/status` | Poll live LangGraph agent execution status. |
| `GET` | `/api/projects/{id}/workflow/compliance` | Get full compliance matrix with evidence. |
| `GET` | `/api/projects/{id}/workflow/proposal` | Get drafted proposal sections & validation report. |
| `POST` | `/api/projects/{id}/workflow/review` | Submit Human-in-the-loop decision (APPROVED / REVISE). |
| `POST` | `/api/assistant/chat` | Send question to AI Copilot. |
| `GET` | `/api/assistant/{id}/history` | Get multi-turn conversation history. |

### Python AI Microservice API (`http://localhost:8000`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Microservice health check. |
| `POST` | `/api/documents/upload` | Ingest PDF/DOCX to ChromaDB vector store. |
| `POST` | `/api/workflow/{project_id}/start` | Execute LangGraph workflow up to human review interrupt. |
| `GET` | `/api/workflow/{project_id}/status` | Query live state snapshot and active stage. |
| `GET` | `/api/workflow/{project_id}/compliance`| Query compliance matrix and objective scores. |
| `GET` | `/api/workflow/{project_id}/proposal` | Query multi-section proposal drafts. |
| `POST` | `/api/workflow/{project_id}/review` | Resume workflow past human review checkpoint. |
| `GET` | `/api/workflow/{project_id}/export/docx`| Download compiled Microsoft Word document. |
| `POST` | `/api/assistant/chat` | AI Copilot conversational engine with tool execution. |
| `GET` | `/api/assistant/{project_id}/history` | Retrieve Copilot chat history. |

---

## 🚀 Step-by-Step Setup & Execution

### 1. Prerequisites
- **Java Development Kit (JDK)**: Java 21 or Java 23 (`java -version`)
- **Python**: Version 3.11 (`python --version`)
- **Node.js**: Version 18+ or 20+ (`node -v`)
- **MySQL**: Running on port 3306 (`rfp_db`)
- **Google Gemini API Key**: Set in environment variables

### 2. Environment Configuration
Create `.env` in `rfp-ai-platform/` (or set environment variables):
```env
DATABASE_URL=mysql+pymysql://rfp_user:sarvyanshu116611@localhost:3306/rfp_db
CHROMA_PERSIST_DIR=./chroma_db
GEMINI_API_KEY=your_gemini_api_key_here
AI_SERVICE_URL=http://localhost:8000
SECRET_KEY=your_jwt_secret_key
```

### 3. Run the Python AI Microservice
```bash
cd rfp-ai-platform/backend
# Activate virtual environment
.\venv\Scripts\activate   # On Windows
# source venv/bin/activate # On Linux/macOS

# Run FastAPI server on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run the Java 21 Spring Boot Backend
```bash
cd rfp-ai-platform/backend-java

# Using Maven
mvn spring-boot:run
```
*The Spring Boot server starts on `http://localhost:8080`.*

### 5. Run the React Frontend
```bash
cd rfp-ai-platform/frontend
npm install
npm run dev
```
*The frontend application opens on `http://localhost:5173`.*

---

## 🧪 Verification & Testing

Execute the comprehensive test suite verifying MCP servers, LangGraph orchestration, human approval interrupts, and end-to-end proposal generation:

```bash
cd rfp-ai-platform/backend
.\venv\Scripts\pytest tests/ -v
```

### Test Suite Summary:
```
============================= test session starts =============================
tests/test_agent_workflow.py::test_make_initial_state PASSED             [  6%]
tests/test_agent_workflow.py::test_routing_should_retry_retrieval PASSED [ 12%]
tests/test_agent_workflow.py::test_routing_should_revise_proposal PASSED [ 18%]
tests/test_agent_workflow.py::test_routing_should_export_or_terminate PASSED [ 25%]
tests/test_agent_workflow.py::test_build_rfp_workflow_graph_structure PASSED [ 31%]
tests/test_db.py::test_db_connection PASSED                              [ 37%]
tests/test_documents.py::test_upload_invalid_file_type PASSED            [ 43%]
tests/test_e2e_agentic_pipeline.py::test_full_agentic_workflow_end_to_end PASSED [ 50%]
tests/test_e2e_agentic_pipeline.py::test_workflow_api_status_and_compliance PASSED [ 56%]
tests/test_e2e_agentic_pipeline.py::test_copilot_assistant_chat_and_history PASSED [ 62%]
tests/test_main.py::test_health_check PASSED                             [ 68%]
tests/test_main.py::test_root PASSED                                     [ 75%]
tests/test_mcp_servers.py::test_mcp_servers_tool_registration PASSED     [ 81%]
tests/test_mcp_servers.py::test_compliance_score_calculation PASSED      [ 87%]
tests/test_mcp_servers.py::test_identify_missing_requirements_gap_analysis PASSED [ 93%]
tests/test_mcp_servers.py::test_proposal_export_docx PASSED              [100%]

============================= 16 passed in 34.72s =============================
```

---

## ⚡ Instant One-Command Startup

You can launch the entire platform with a single command from the project root:

### Windows Batch / Double-Click:
```cmd
run.bat
```

### PowerShell:
```powershell
.\run.ps1
```

### Python:
```bash
python run.py
```

*This automatically boots the Python FastAPI backend, launches the React Vite frontend, verifies service health, and opens **`http://localhost:5173`** in your browser.*

---

## 📄 License
This project is licensed under the MIT License.
