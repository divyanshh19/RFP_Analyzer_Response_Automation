"""
Conditional Routing Functions for the LangGraph RFP Workflow.
"""

from app.services.agent.state import RFPWorkflowState, WorkflowExecutionState


def should_proceed_after_ingestion(state: RFPWorkflowState) -> str:
    """Halt execution if document ingestion failed; otherwise proceed to requirement analysis."""
    if state.get("execution_state") in [WorkflowExecutionState.FAILED.value, WorkflowExecutionState.BLOCKED.value]:
        return "halt"
    if not state.get("raw_text"):
        return "halt"
    return "proceed_to_requirements"


def should_proceed_after_requirements(state: RFPWorkflowState) -> str:
    """Halt execution if requirement extraction failed or was blocked; otherwise proceed to retrieval."""
    if state.get("execution_state") in [WorkflowExecutionState.FAILED.value, WorkflowExecutionState.BLOCKED.value]:
        return "halt"
    reqs = state.get("requirements", [])
    if not reqs:
        return "halt"
    return "proceed_to_retrieval"


def should_proceed_after_compliance(state: RFPWorkflowState) -> str:
    """Halt execution if compliance assessment failed or was blocked; otherwise proceed to gap analysis."""
    if state.get("execution_state") in [WorkflowExecutionState.FAILED.value, WorkflowExecutionState.BLOCKED.value]:
        return "halt"
    comp_matrix = state.get("compliance_matrix", [])
    if not comp_matrix:
        return "halt"
    return "proceed_to_gaps"


def should_retry_retrieval(state: RFPWorkflowState) -> str:
    """
    Decides whether the Gap Analysis Agent should trigger another retrieval cycle
    with expanded queries or proceed to Proposal Generation.
    """
    gaps = state.get("identified_gaps", [])
    iterations = state.get("retrieval_iterations", 0)
    max_retries = state.get("max_retrieval_retries", 2)
    
    # If there are gaps that might be remediated and we haven't exceeded max retries
    if gaps and iterations < max_retries:
        return "retry_retrieval"
    return "proceed_to_proposal"


def should_revise_proposal(state: RFPWorkflowState) -> str:
    """
    Decides whether the Proposal Validation Agent should route back to Proposal Generation
    to correct unsupported assertions or proceed to Human Review.
    """
    val = state.get("validation_results", {})
    is_valid = val.get("is_valid", True)
    iterations = state.get("generation_iterations", 0)
    max_retries = state.get("max_generation_retries", 2)
    
    if not is_valid and iterations < max_retries:
        return "revise_proposal"
    return "request_human_review"


def should_export_or_terminate(state: RFPWorkflowState) -> str:
    """
    Evaluates human approval decision at the Human Review Interrupt Checkpoint.
    """
    status = state.get("human_review_status", "PENDING").upper()
    if status == "APPROVED":
        return "proceed_to_export"
    elif status == "REVISE":
        return "revise_proposal"
    return "terminate"
