"""
Shared State Schema for the LangGraph 9-Agent RFP Workflow.
"""

from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime, timezone


class WorkflowExecutionState(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    BLOCKED = "Blocked"


class RFPWorkflowState(TypedDict, total=False):
    # Core Metadata
    project_id: str
    document_id: str
    file_path: str
    file_type: str
    
    # Execution Lifecycle & Error Isolation
    execution_state: str # WorkflowExecutionState value: "Pending", "Running", "Completed", "Failed", "Blocked"
    current_stage: str
    blocked_reason: Optional[str]
    retry_stage: Optional[str]
    
    # 1. Document Ingestion
    raw_text: str
    total_pages: int
    char_count: int
    needs_ocr: bool
    
    # 2. Requirement Analysis
    requirements: List[Dict[str, Any]]
    deadlines: List[Dict[str, Any]]
    eligibility_criteria: List[Dict[str, Any]]
    evaluation_criteria: List[Dict[str, Any]]
    mandatory_documents: List[Dict[str, Any]]
    
    # 3. Knowledge Retrieval
    retrieved_evidence: Dict[str, List[Dict[str, Any]]] # requirement_id -> [evidence chunks]
    retrieval_iterations: int
    max_retrieval_retries: int
    
    # 4. Compliance Analysis
    compliance_matrix: List[Dict[str, Any]] # status, score, rationale, evidence
    compliance_score_metrics: Dict[str, Any] # overall_score, breakdown counts
    
    # 5. Gap Analysis
    identified_gaps: List[Dict[str, Any]]
    gap_summary: str
    
    # 6. Proposal Generation
    draft_responses: Dict[str, str] # requirement_id -> draft response
    draft_sections: List[Dict[str, Any]] # [{section_name: str, content: str}]
    generation_iterations: int
    max_generation_retries: int
    
    # 7. Proposal Validation
    validation_results: Dict[str, Any] # is_valid, unsupported_claims, critique, coverage
    
    # 8. Human Review (Interrupt Checkpoint)
    human_review_status: str # "PENDING", "APPROVED", "REVISE", "REJECTED"
    human_feedback: Optional[str]
    reviewed_at: Optional[str]
    
    # 9. Export
    export_file_path: Optional[str]
    export_file_name: Optional[str]
    
    # Workflow Tracing & Observability
    workflow_status: str # Active stage name or COMPLETED / FAILED
    stage_history: List[Dict[str, Any]]
    errors: List[str]
    updated_at: str


def make_initial_state(
    project_id: str,
    document_id: str,
    file_path: str,
    file_type: str = "pdf",
    max_retrieval_retries: int = 2,
    max_generation_retries: int = 2
) -> RFPWorkflowState:
    """Factory helper to build a fresh, typed initial state."""
    return {
        "project_id": str(project_id),
        "document_id": str(document_id),
        "file_path": file_path,
        "file_type": file_type,
        "execution_state": WorkflowExecutionState.PENDING.value,
        "current_stage": "INITIALIZED",
        "blocked_reason": None,
        "retry_stage": None,
        "raw_text": "",
        "total_pages": 0,
        "char_count": 0,
        "needs_ocr": False,
        "requirements": [],
        "deadlines": [],
        "eligibility_criteria": [],
        "evaluation_criteria": [],
        "mandatory_documents": [],
        "retrieved_evidence": {},
        "retrieval_iterations": 0,
        "max_retrieval_retries": max_retrieval_retries,
        "compliance_matrix": [],
        "compliance_score_metrics": {},
        "identified_gaps": [],
        "gap_summary": "",
        "draft_responses": {},
        "draft_sections": [],
        "generation_iterations": 0,
        "max_generation_retries": max_generation_retries,
        "validation_results": {},
        "human_review_status": "PENDING",
        "human_feedback": None,
        "reviewed_at": None,
        "export_file_path": None,
        "export_file_name": None,
        "workflow_status": "INITIALIZED",
        "stage_history": [],
        "errors": [],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
