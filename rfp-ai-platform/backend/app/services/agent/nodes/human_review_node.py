"""
Human Review Agent Node (Human-in-the-Loop Checkpoint).
Presents the validated proposal draft and compliance matrix for human review.
Captures user decision (APPROVED, REVISE, REJECTED) and feedback to direct subsequent workflow edges.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState


def human_review_node(state: RFPWorkflowState) -> dict:
    """
    Executes Stage 8: Human Review Checkpoint.
    If the review decision is already provided (upon resumption), records it;
    otherwise sets the status to AWAITING_HUMAN_APPROVAL.
    """
    review_status = state.get("human_review_status", "PENDING").upper()
    feedback = state.get("human_feedback")
    
    stage_entry = {
        "stage": "HUMAN_REVIEW",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": review_status
    }
    
    if review_status == "PENDING":
        stage_entry["summary"] = "Workflow paused at human checkpoint. Awaiting human approval or revision instructions."
        return {
            "workflow_status": "AWAITING_HUMAN_APPROVAL",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    elif review_status == "APPROVED":
        stage_entry["status"] = "COMPLETED"
        stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
        stage_entry["summary"] = f"Human reviewer approved the proposal for export. Feedback: {feedback or 'None'}"
        return {
            "human_review_status": "APPROVED",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_status": "HUMAN_APPROVED",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    elif review_status == "REVISE":
        stage_entry["status"] = "REVISION_REQUESTED"
        stage_entry["summary"] = f"Human reviewer requested proposal revision: '{feedback}'"
        return {
            "human_review_status": "REVISE",
            "human_feedback": feedback,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_status": "REVISION_REQUESTED",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    else: # REJECTED
        stage_entry["status"] = "TERMINATED"
        stage_entry["summary"] = f"Human reviewer rejected the proposal: '{feedback}'"
        return {
            "human_review_status": "REJECTED",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_status": "REJECTED_TERMINATED",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
