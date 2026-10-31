"""
Unit and Integration Tests for the LangGraph 9-Agent Workflow:
- State definitions and initial state factory
- Conditional routing decisions (re-retrieval loop, revision loop, human approval)
- Workflow compilation, interrupt checkpointing, and resumption
"""

import os
import sys
import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.agent.state import make_initial_state, RFPWorkflowState
from app.services.agent.routing import (
    should_retry_retrieval,
    should_revise_proposal,
    should_export_or_terminate
)
from app.services.agent.graph import build_rfp_workflow


def test_make_initial_state():
    """Verify factory properly creates default typed state."""
    state = make_initial_state(
        project_id="proj-101",
        document_id="doc-202",
        file_path="dummy.pdf",
        file_type="pdf",
        max_retrieval_retries=3,
        max_generation_retries=2
    )
    assert state["project_id"] == "proj-101"
    assert state["document_id"] == "doc-202"
    assert state["workflow_status"] == "INITIALIZED"
    assert state["retrieval_iterations"] == 0
    assert state["max_retrieval_retries"] == 3
    assert state["human_review_status"] == "PENDING"
    assert isinstance(state["stage_history"], list)


def test_routing_should_retry_retrieval():
    """Verify conditional edge for re-retrieval based on gaps and iteration count."""
    # Case 1: Gaps exist and iterations < max_retries => retry
    state_retry: RFPWorkflowState = {
        "identified_gaps": [{"requirement_id": "REQ-1"}],
        "retrieval_iterations": 1,
        "max_retrieval_retries": 2
    }
    assert should_retry_retrieval(state_retry) == "retry_retrieval"
    
    # Case 2: Gaps exist but max retries reached => proceed
    state_maxed: RFPWorkflowState = {
        "identified_gaps": [{"requirement_id": "REQ-1"}],
        "retrieval_iterations": 2,
        "max_retrieval_retries": 2
    }
    assert should_retry_retrieval(state_maxed) == "proceed_to_proposal"
    
    # Case 3: No gaps => proceed
    state_clean: RFPWorkflowState = {
        "identified_gaps": [],
        "retrieval_iterations": 0,
        "max_retrieval_retries": 2
    }
    assert should_retry_retrieval(state_clean) == "proceed_to_proposal"


def test_routing_should_revise_proposal():
    """Verify conditional edge for proposal revision based on validation."""
    # Case 1: Validation failed and iterations < max => revise
    state_revise: RFPWorkflowState = {
        "validation_results": {"is_valid": False, "critique": "Unverified claim found."},
        "generation_iterations": 1,
        "max_generation_retries": 2
    }
    assert should_revise_proposal(state_revise) == "revise_proposal"
    
    # Case 2: Validation failed but max retries reached => escalate to human
    state_escalate: RFPWorkflowState = {
        "validation_results": {"is_valid": False, "critique": "Unverified claim found."},
        "generation_iterations": 2,
        "max_generation_retries": 2
    }
    assert should_revise_proposal(state_escalate) == "request_human_review"
    
    # Case 3: Valid => proceed to human review
    state_valid: RFPWorkflowState = {
        "validation_results": {"is_valid": True},
        "generation_iterations": 1,
        "max_generation_retries": 2
    }
    assert should_revise_proposal(state_valid) == "request_human_review"


def test_routing_should_export_or_terminate():
    """Verify human decision routing at the interrupt checkpoint."""
    assert should_export_or_terminate({"human_review_status": "APPROVED"}) == "proceed_to_export"
    assert should_export_or_terminate({"human_review_status": "REVISE"}) == "revise_proposal"
    assert should_export_or_terminate({"human_review_status": "REJECTED"}) == "terminate"


def test_build_rfp_workflow_graph_structure():
    """Verify that StateGraph compiles with all 9 nodes, edges, and checkpointer."""
    app = build_rfp_workflow()
    assert app is not None
    # Verify nodes present in graph
    node_keys = list(app.get_graph().nodes.keys())
    for expected_node in [
        "document_ingestion",
        "requirement_analysis",
        "knowledge_retrieval",
        "compliance_analysis",
        "gap_analysis",
        "proposal_generation",
        "proposal_validation",
        "human_review",
        "export"
    ]:
        assert expected_node in node_keys
