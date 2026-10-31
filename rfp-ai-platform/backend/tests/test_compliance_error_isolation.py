"""
Regression Tests: Compliance Error Isolation & Anti-Hallucination Guardrails.
Guarantees that:
1. Infrastructure exceptions, API errors, and 429 RESOURCE_EXHAUSTED errors NEVER become RFP requirements.
2. Synthetic requirements like ERR-001 are NEVER created from exceptions.
3. API errors NEVER get classified as 'Requires Clarification' or assigned a 50% score.
4. Compliance scores remain 'None' (N/A) when no genuine assessed requirements exist.
5. The LangGraph workflow halts in 'Blocked' or 'Failed' state with retry capabilities.
"""

import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.services.agent.state import RFPWorkflowState, WorkflowExecutionState, make_initial_state
from app.services.agent.nodes.requirements_node import requirement_analysis_node
from app.services.agent.nodes.compliance_node import compliance_analysis_node
from app.services.agent.routing import should_proceed_after_requirements, should_proceed_after_compliance
from app.mcp.compliance_server import calculate_compliance_score, identify_missing_requirements, ComplianceStatus
from app.services.agent.workflow_manager import workflow_manager
from app.services.agent.graph import rfp_workflow_app


def test_gemini_429_quota_exhaustion_does_not_create_err001_or_synthetic_requirements():
    """
    REGRESSION TEST:
    When Gemini API raises HTTP 429 RESOURCE_EXHAUSTED during requirement extraction:
    - Requirements list must remain EMPTY.
    - ERR-001 or synthetic error requirements must NEVER be generated.
    - Execution state must transition to 'Blocked'.
    - Stage status must be 'BLOCKED'.
    """
    initial_state = make_initial_state(
        project_id="test_quota_proj",
        document_id="test_doc",
        file_path="dummy.docx"
    )
    initial_state["raw_text"] = "Section 1: The vendor must provide 24/7 technical support."

    # Simulate Gemini API 429 Resource Exhausted exception
    quota_error_msg = "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota'}}"
    with patch("app.services.extraction.requirement_extractor.extract_requirements_from_text") as mock_extractor:
        mock_extractor.side_effect = Exception(quota_error_msg)
        
        result = requirement_analysis_node(initial_state)

    # 1. State must be BLOCKED
    assert result["execution_state"] == WorkflowExecutionState.BLOCKED.value
    assert result["workflow_status"] == "REQUIREMENT_ANALYSIS_BLOCKED"
    assert "429 RESOURCE_EXHAUSTED" in result["blocked_reason"]
    assert result["retry_stage"] == "REQUIREMENT_ANALYSIS"

    # 2. Requirements MUST BE EMPTY (Never ERR-001!)
    assert result["requirements"] == [], "Requirements list must be strictly empty on extraction failure"
    assert not any(r.get("requirement_id") == "ERR-001" for r in result["requirements"])
    assert not any("error" in str(r).lower() for r in result["requirements"])


def test_compliance_score_is_na_when_no_valid_requirements_exist():
    """
    REGRESSION TEST:
    When no valid requirements have been assessed:
    - Overall score must be None (rendered as N/A in UI), NEVER 0% or 50%.
    - Mandatory compliance score must be None (N/A).
    - Even if a synthetic ERR-001 dictionary was passed, it must be ignored.
    """
    # Case 1: Empty compliance matrix
    empty_metrics = calculate_compliance_score([])
    assert empty_metrics["overall_score"] is None, "Overall score must be None (N/A) when empty"
    assert empty_metrics["mandatory_compliance_score"] is None
    assert empty_metrics["is_valid"] is False
    assert empty_metrics["total_requirements"] == 0

    # Case 2: Attempting to pass an error item
    poisoned_matrix = [
        {
            "requirement_id": "ERR-001",
            "description": "Failed to parse requirements",
            "status": "Requires clarification",
            "compliance_score": 0.5
        }
    ]
    safe_metrics = calculate_compliance_score(poisoned_matrix)
    assert safe_metrics["overall_score"] is None, "Synthetic error item must be filtered out resulting in None"
    assert safe_metrics["total_requirements"] == 0
    assert safe_metrics["is_valid"] is False


def test_gemini_429_during_compliance_evaluation_does_not_classify_as_clarification():
    """
    REGRESSION TEST:
    If Gemini throws 429 RESOURCE_EXHAUSTED during compliance assessment:
    - The requirement must NEVER be classified as 'Requires Clarification'.
    - Score must NEVER be fabricated as 0.5 (50%).
    - Execution state must transition to 'Blocked'.
    """
    valid_reqs = [
        {
            "requirement_id": "REQ-001",
            "description": "Must provide 99.9% uptime SLA.",
            "category": "Technical",
            "mandatory": True
        }
    ]
    
    state = make_initial_state(
        project_id="test_compliance_proj",
        document_id="test_doc",
        file_path="dummy.docx"
    )
    state["requirements"] = valid_reqs
    state["retrieved_evidence"] = {"REQ-001": [{"chunk_id": "c1", "text": "We provide 99.9% SLA."}]}

    # Simulate Gemini 429 quota exception during compliance assessment
    with patch("app.mcp.compliance_server._get_gemini_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        mock_client_factory.return_value = mock_client

        result = compliance_analysis_node(state)

    # 1. Must be Blocked
    assert result["execution_state"] == WorkflowExecutionState.BLOCKED.value
    assert result["workflow_status"] == "COMPLIANCE_ANALYSIS_BLOCKED"
    assert "429 RESOURCE_EXHAUSTED" in result["blocked_reason"]

    # 2. Compliance matrix must be empty (NOT classified as clarification!)
    assert result["compliance_matrix"] == []
    assert result["compliance_score_metrics"]["overall_score"] is None, "Score must be None (N/A)"


def test_workflow_graph_halts_when_extraction_blocked():
    """
    REGRESSION TEST:
    When requirement extraction is blocked or fails, the LangGraph workflow must
    halt immediately and NEVER execute knowledge retrieval or proposal generation.
    """
    pid = str(uuid.uuid4())
    config = {"configurable": {"thread_id": pid}}
    
    init_state = make_initial_state(
        project_id=pid,
        document_id="doc-123",
        file_path="sample.docx",
        file_type="docx"
    )
    init_state["raw_text"] = "Dummy RFP document text."
    
    # Mock extract_requirements to raise 429 Resource Exhausted
    with patch("app.services.extraction.requirement_extractor.extract_requirements_from_text") as mock_extract:
        mock_extract.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        
        final_state = rfp_workflow_app.invoke(init_state, config=config)

    # Check workflow stopped at requirement analysis
    assert final_state["execution_state"] == WorkflowExecutionState.BLOCKED.value
    assert final_state["requirements"] == []
    assert final_state["compliance_matrix"] == []
    
    # Verify downstream stages were NEVER executed
    stages_run = [s.get("stage") for s in final_state.get("stage_history", [])]
    assert "REQUIREMENT_ANALYSIS" in stages_run
    assert not any("KNOWLEDGE_RETRIEVAL" in s for s in stages_run), "Retrieval must NOT run on blocked requirements"
    assert "COMPLIANCE_ANALYSIS" not in stages_run, "Compliance must NOT run on blocked requirements"
    assert not any("PROPOSAL_GENERATION" in s for s in stages_run), "Proposal generation must NOT run"


def test_genuine_compliance_scoring_mathematical_precision():
    """
    Verifies that genuine requirements are correctly and objectively scored.
    """
    genuine_matrix = [
        {
            "requirement_id": "REQ-1",
            "description": "SOC 2 Type II certified",
            "status": ComplianceStatus.COMPLIANT,
            "compliance_score": 1.0,
            "mandatory": True
        },
        {
            "requirement_id": "REQ-2",
            "description": "FedRAMP High certified",
            "status": ComplianceStatus.NON_COMPLIANT,
            "compliance_score": 0.0,
            "mandatory": True
        },
        {
            "requirement_id": "REQ-3",
            "description": "Hybrid cloud deployment supported",
            "status": ComplianceStatus.PARTIALLY_COMPLIANT,
            "compliance_score": 0.5,
            "mandatory": False
        },
        {
            "requirement_id": "REQ-4",
            "description": "Custom API integration SLA ambiguous in tender",
            "status": ComplianceStatus.REQUIRES_CLARIFICATION,
            "compliance_score": 0.5,
            "mandatory": False
        }
    ]

    metrics = calculate_compliance_score(genuine_matrix)
    assert metrics["is_valid"] is True
    assert metrics["total_requirements"] == 4
    assert metrics["compliant_count"] == 1
    assert metrics["non_compliant_count"] == 1
    assert metrics["partially_compliant_count"] == 1
    assert metrics["clarification_count"] == 1
    # Overall = (1.0 + 0.0 + 0.5 + 0.5) / 4 = 2.0 / 4 = 50.0%
    assert metrics["overall_score"] == 50.0
    # Mandatory = (1.0 + 0.0) / 2 = 1.0 / 2 = 50.0%
    assert metrics["mandatory_compliance_score"] == 50.0
