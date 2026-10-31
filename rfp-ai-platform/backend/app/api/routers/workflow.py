"""
FastAPI Router for LangGraph Agentic Workflow Orchestration.
Exposes endpoints to initiate workflows, stream/poll live state, inspect compliance metrics,
and submit human-in-the-loop approvals or revision requests.
"""

import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.api.deps import SessionDep, CurrentUser
from app.models.rfp import RFPProject
from app.models.document import Document, DocumentType
from app.services.agent.workflow_manager import workflow_manager

router = APIRouter(prefix="/workflow", tags=["workflow"])


class WorkflowStartRequest(BaseModel):
    document_id: Optional[uuid.UUID] = None


class HumanReviewRequest(BaseModel):
    action: str # "APPROVED", "REVISE", "REJECTED"
    feedback: Optional[str] = None


@router.post("/{project_id}/start")
def start_project_workflow(
    project_id: uuid.UUID,
    data: WorkflowStartRequest,
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    """
    Initiates the 9-agent LangGraph workflow for an RFP project.
    Runs until the human review interrupt checkpoint.
    """
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    doc_id = data.document_id
    if not doc_id:
        doc = db.query(Document).filter(
            Document.rfp_project_id == project_id,
            Document.document_type == DocumentType.RFP
        ).order_by(Document.created_at.desc()).first()
        if not doc:
            raise HTTPException(status_code=400, detail="No RFP document found for this project. Please upload one first.")
        doc_id = doc.id
    else:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
    # Execute workflow until human review interrupt
    result = workflow_manager.start_workflow(
        project_id=str(project_id),
        document_id=str(doc.id),
        file_path=doc.file_path,
        file_type=doc.file_type
    )
    return result


@router.get("/{project_id}/status")
def get_project_workflow_status(project_id: uuid.UUID, current_user: CurrentUser):
    """Retrieves live LangGraph agent execution status, stage history, and execution state."""
    state = workflow_manager.get_workflow_state(str(project_id))
    if not state:
        return {
            "project_id": str(project_id),
            "execution_state": "Pending",
            "workflow_status": "NOT_STARTED",
            "current_stage": "INITIALIZED",
            "blocked_reason": None,
            "retry_stage": None,
            "stage_history": [],
            "next_node": None,
            "compliance_score": None,
            "mandatory_score": None,
            "total_requirements": 0,
            "errors": []
        }
        
    metrics = state.get("compliance_score_metrics", {})
    return {
        "project_id": str(project_id),
        "execution_state": state.get("execution_state", "Pending"),
        "workflow_status": state.get("workflow_status"),
        "current_stage": state.get("current_stage"),
        "blocked_reason": state.get("blocked_reason"),
        "retry_stage": state.get("retry_stage"),
        "stage_history": state.get("stage_history", []),
        "next_node": state.get("next_node"),
        "compliance_score": metrics.get("overall_score"),
        "mandatory_score": metrics.get("mandatory_compliance_score"),
        "total_requirements": len(state.get("requirements", [])),
        "gaps_count": len(state.get("identified_gaps", [])),
        "human_review_status": state.get("human_review_status"),
        "export_file_path": state.get("export_file_path"),
        "export_file_name": state.get("export_file_name"),
        "errors": state.get("errors", [])
    }


@router.get("/{project_id}/compliance")
def get_project_compliance_report(project_id: uuid.UUID, current_user: CurrentUser):
    """Retrieves full compliance matrix and evidence citations for the project."""
    state = workflow_manager.get_workflow_state(str(project_id))
    if not state:
        return {
            "project_id": str(project_id),
            "execution_state": "Pending",
            "blocked_reason": None,
            "metrics": {
                "overall_score": None,
                "mandatory_compliance_score": None,
                "total_requirements": 0,
                "compliant_count": 0,
                "partially_compliant_count": 0,
                "non_compliant_count": 0,
                "clarification_count": 0,
                "is_valid": False,
                "audit_summary": "No valid compliance assessment exists."
            },
            "compliance_matrix": [],
            "identified_gaps": []
        }
        
    metrics = state.get("compliance_score_metrics") or {
        "overall_score": None,
        "mandatory_compliance_score": None,
        "total_requirements": len(state.get("requirements", [])),
        "compliant_count": 0,
        "partially_compliant_count": 0,
        "non_compliant_count": 0,
        "clarification_count": 0,
        "is_valid": False,
        "audit_summary": state.get("blocked_reason") or "No valid compliance assessment exists."
    }
    
    return {
        "project_id": str(project_id),
        "execution_state": state.get("execution_state", "Pending"),
        "blocked_reason": state.get("blocked_reason"),
        "retry_stage": state.get("retry_stage"),
        "metrics": metrics,
        "compliance_matrix": state.get("compliance_matrix", []),
        "identified_gaps": state.get("identified_gaps", [])
    }


@router.post("/{project_id}/retry")
def retry_project_workflow(project_id: uuid.UUID, current_user: CurrentUser):
    """
    Retries a blocked or failed workflow stage once API quota or dependency is restored.
    """
    result = workflow_manager.retry_workflow(str(project_id))
    return result


@router.get("/{project_id}/proposal")
def get_project_proposal_draft(project_id: uuid.UUID, current_user: CurrentUser):
    """Retrieves drafted proposal sections, validation critique, and export package info."""
    state = workflow_manager.get_workflow_state(str(project_id))
    if not state or not state.get("draft_sections"):
        raise HTTPException(status_code=404, detail="Proposal draft has not been generated for this project.")
        
    return {
        "project_id": str(project_id),
        "sections": state.get("draft_sections", []),
        "draft_responses": state.get("draft_responses", {}),
        "validation_results": state.get("validation_results", {}),
        "human_review_status": state.get("human_review_status"),
        "export_file_path": state.get("export_file_path"),
        "export_file_name": state.get("export_file_name")
    }


@router.post("/{project_id}/review")
def submit_human_review_decision(
    project_id: uuid.UUID,
    data: HumanReviewRequest,
    current_user: CurrentUser
):
    """
    Submits a human approval decision (APPROVED, REVISE, REJECTED) with optional feedback.
    Resumes LangGraph execution past the interrupt checkpoint.
    """
    result = workflow_manager.resume_human_review(
        project_id=str(project_id),
        action=data.action,
        feedback=data.feedback
    )
    return result
