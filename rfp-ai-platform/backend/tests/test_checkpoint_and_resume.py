"""
Comprehensive LangGraph Checkpoint Persistence & Node Resume Test Suite.
Verifies that:
1. Workflow state is genuinely checkpointed when Gemini returns HTTP 429.
2. Retry resumes strictly from the failed COMPLIANCE_ANALYSIS node without restarting earlier nodes.
3. Extracted requirements, raw text, and retrieved evidence are completely preserved.
4. No duplicate requirements, documents, or compliance records are created.
5. State query functions retrieve actual persisted checkpoint data.
6. Execution proceeds through human review checkpoint to completion.
"""

import uuid
from unittest.mock import patch, MagicMock
import pytest

from app.services.agent.graph import rfp_workflow_app
from app.services.agent.state import make_initial_state, WorkflowExecutionState
from app.services.agent.workflow_manager import workflow_manager
from app.mcp.client import mcp_client
from app.mcp.compliance_server import ComplianceStatus


def test_compliance_429_checkpoint_and_resumption_lifecycle():
    """
    Full lifecycle test verifying:
    Step 1: Normal execution of Stages 1, 2, 3 (Ingestion, Requirements, Retrieval).
    Step 2: Simulated 429 Quota Exhaustion at Stage 4 (Compliance Analysis).
    Step 3: Verification of Checkpoint State (Blocked, preserved data, no synthetic ERR-001).
    Step 4: Retry execution resuming from COMPLIANCE_ANALYSIS (Stages 1-3 MUST NOT re-run).
    Step 5: Successful completion to human review interrupt and subsequent final export.
    """
    project_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": project_id}}

    # Track invocations of each node to verify which nodes run
    executed_nodes = []

    # Mock sample document text and requirements
    sample_text = "The vendor must provide SOC 2 Type II compliance and 99.9% availability."
    sample_reqs = [
        {
            "requirement_id": "REQ-1",
            "description": "SOC 2 Type II compliance certified",
            "category": "Compliance",
            "mandatory": True,
            "priority": "HIGH"
        },
        {
            "requirement_id": "REQ-2",
            "description": "99.9% service availability SLA",
            "category": "Technical",
            "mandatory": True,
            "priority": "HIGH"
        }
    ]
    sample_evidence = {
        "REQ-1": [{"chunk_id": "chk-1", "text": "We maintain SOC 2 Type II audit reports annually.", "document_type": "KNOWLEDGE_BASE"}],
        "REQ-2": [{"chunk_id": "chk-2", "text": "We guarantee 99.95% uptime with financial penalties.", "document_type": "KNOWLEDGE_BASE"}]
    }
    sample_compliance_matrix = [
        {
            "requirement_id": "REQ-1",
            "description": "SOC 2 Type II compliance certified",
            "status": ComplianceStatus.COMPLIANT,
            "compliance_score": 1.0,
            "mandatory": True,
            "citations": ["SOC 2 audit report"]
        },
        {
            "requirement_id": "REQ-2",
            "description": "99.9% service availability SLA",
            "status": ComplianceStatus.COMPLIANT,
            "compliance_score": 1.0,
            "mandatory": True,
            "citations": ["99.95% uptime guarantee"]
        }
    ]

    # Initialize state
    init_state = make_initial_state(
        project_id=project_id,
        document_id=doc_id,
        file_path="rfp_doc.docx",
        file_type="docx"
    )

    # =========================================================================
    # STEP 1 & 2: Run workflow until Compliance hits HTTP 429
    # =========================================================================
    with patch.object(mcp_client, "get_tool") as mock_get_tool:
        def side_effect_tools(name):
            tool = MagicMock()
            if name == "extract_rfp_text":
                def invoke_ingest(args):
                    executed_nodes.append("document_ingestion")
                    return {"success": True, "text": sample_text, "word_count": 15}
                tool.invoke.side_effect = invoke_ingest
                return tool
            elif name == "extract_rfp_requirements":
                def invoke_reqs(args):
                    executed_nodes.append("requirement_analysis")
                    return sample_reqs
                tool.invoke.side_effect = invoke_reqs
                return tool
            elif name in ["search_supporting_evidence", "retrieve_company_capabilities", "retrieve_certifications"]:
                def invoke_retrieval(args):
                    if "knowledge_retrieval" not in executed_nodes:
                        executed_nodes.append("knowledge_retrieval")
                    req_text = args.get("requirement_text", "")
                    if "SOC" in req_text:
                        return sample_evidence["REQ-1"]
                    elif "99.9" in req_text:
                        return sample_evidence["REQ-2"]
                    return []
                tool.invoke.side_effect = invoke_retrieval
                return tool
            elif name == "map_requirements_to_capabilities":
                def invoke_comp(args):
                    executed_nodes.append("compliance_analysis")
                    # Simulate Gemini 429 Quota Exhaustion
                    raise RuntimeError("429 RESOURCE_EXHAUSTED: You exceeded your current quota")
                tool.invoke.side_effect = invoke_comp
                return tool
            elif name == "calculate_compliance_score":
                return MagicMock()
            return None

        mock_get_tool.side_effect = side_effect_tools

        # Start workflow
        res1 = workflow_manager.start_workflow(
            project_id=project_id,
            document_id=doc_id,
            file_path="rfp_doc.docx",
            file_type="docx"
        )

    # Verify execution was stopped and marked as Blocked
    assert res1["execution_state"] == WorkflowExecutionState.BLOCKED.value
    assert res1["current_stage"] == "COMPLIANCE_ANALYSIS"
    assert "429" in res1["blocked_reason"]
    assert res1["retry_stage"] == "COMPLIANCE_ANALYSIS"
    assert res1["compliance_score"] is None

    # Check which nodes ran up to this point
    assert "document_ingestion" in executed_nodes
    assert "requirement_analysis" in executed_nodes
    assert "knowledge_retrieval" in executed_nodes
    assert "compliance_analysis" in executed_nodes

    # =========================================================================
    # STEP 3: Confirm LangGraph Checkpoint Persistence
    # =========================================================================
    persisted_state = workflow_manager.get_workflow_state(project_id)
    assert persisted_state is not None, "State must be persisted in checkpointer"
    assert persisted_state["execution_state"] == WorkflowExecutionState.BLOCKED.value
    assert persisted_state["current_stage"] == "COMPLIANCE_ANALYSIS"
    assert persisted_state["retry_stage"] == "COMPLIANCE_ANALYSIS"

    # CRITICAL: Verify previously completed stages' data is fully preserved
    assert persisted_state["raw_text"] == sample_text
    assert len(persisted_state["requirements"]) == 2
    assert persisted_state["requirements"][0]["requirement_id"] == "REQ-1"
    assert persisted_state["retrieved_evidence"] == sample_evidence
    # Anti-hallucination guarantee: No synthetic requirements or fake scores
    assert persisted_state["compliance_matrix"] == []
    assert not any("ERR-" in str(r.get("requirement_id", "")) for r in persisted_state["requirements"])

    # =========================================================================
    # STEP 4: Retry Workflow - Must resume strictly from COMPLIANCE_ANALYSIS
    # =========================================================================
    # Reset execution tracker to ensure earlier nodes are NOT called again
    executed_nodes.clear()

    with patch.object(mcp_client, "get_tool") as mock_get_tool:
        def side_effect_resume(name):
            tool = MagicMock()
            if name == "extract_rfp_text":
                def invoke_ingest(args):
                    executed_nodes.append("document_ingestion")
                    return {"success": True, "text": sample_text}
                tool.invoke.side_effect = invoke_ingest
                return tool
            elif name == "extract_rfp_requirements":
                def invoke_reqs(args):
                    executed_nodes.append("requirement_analysis")
                    return sample_reqs
                tool.invoke.side_effect = invoke_reqs
                return tool
            elif name in ["search_supporting_evidence", "retrieve_company_capabilities", "retrieve_certifications"]:
                def invoke_retrieval(args):
                    if "knowledge_retrieval" not in executed_nodes:
                        executed_nodes.append("knowledge_retrieval")
                    req_text = args.get("requirement_text", "")
                    if "SOC" in req_text:
                        return sample_evidence["REQ-1"]
                    elif "99.9" in req_text:
                        return sample_evidence["REQ-2"]
                    return []
                tool.invoke.side_effect = invoke_retrieval
                return tool
            elif name == "map_requirements_to_capabilities":
                def invoke_comp(args):
                    executed_nodes.append("compliance_analysis")
                    # LLM Quota restored: returns genuine compliance assessment
                    return sample_compliance_matrix
                tool.invoke.side_effect = invoke_comp
                return tool
            elif name == "calculate_compliance_score":
                tool.invoke.return_value = {
                    "overall_score": 100.0,
                    "mandatory_compliance_score": 100.0,
                    "total_requirements": 2,
                    "compliant_count": 2,
                    "partially_compliant_count": 0,
                    "non_compliant_count": 0,
                    "clarification_count": 0,
                    "is_valid": True,
                    "audit_summary": "2 Compliant out of 2 requirements."
                }
                return tool
            elif name == "identify_missing_requirements":
                def invoke_gaps(args):
                    executed_nodes.append("gap_analysis")
                    return []  # No gaps
                tool.invoke.side_effect = invoke_gaps
                return tool
            elif name == "generate_proposal_section":
                def invoke_draft(args):
                    if "proposal_generation" not in executed_nodes:
                        executed_nodes.append("proposal_generation")
                    return {"content": "Executive Summary and Proposal Narrative."}
                tool.invoke.side_effect = invoke_draft
                return tool
            elif name == "validate_proposal_content":
                def invoke_val(args):
                    if "proposal_validation" not in executed_nodes:
                        executed_nodes.append("proposal_validation")
                    return {"is_valid": True, "unsupported_claims": [], "critique": ""}
                tool.invoke.side_effect = invoke_val
                return tool
            elif name == "validate_response_coverage":
                tool.invoke.return_value = {"coverage_ratio": 1.0, "is_complete": True, "missing_requirements": []}
                return tool
            return None

        mock_get_tool.side_effect = side_effect_resume

        # Execute retry
        retry_res = workflow_manager.retry_workflow(project_id)

    # 1. VERIFY RESUME POINT: Document ingestion, requirements extraction, and knowledge retrieval WERE NOT RE-RUN
    assert "document_ingestion" not in executed_nodes, "Document ingestion must NOT re-run on retry!"
    assert "requirement_analysis" not in executed_nodes, "Requirement analysis must NOT re-run on retry!"
    assert "knowledge_retrieval" not in executed_nodes, "Knowledge retrieval must NOT re-run on retry!"

    # 2. VERIFY COMPLIANCE & DOWNSTREAM RAN
    assert "compliance_analysis" in executed_nodes, "Compliance analysis must be re-executed!"
    assert "gap_analysis" in executed_nodes
    assert "proposal_generation" in executed_nodes
    assert "proposal_validation" in executed_nodes

    # 3. VERIFY NO DUPLICATION
    state_after_retry = workflow_manager.get_workflow_state(project_id)
    assert len(state_after_retry["requirements"]) == 2, "Requirements count must remain exactly 2 without duplication"
    assert len(state_after_retry["compliance_matrix"]) == 2, "Compliance matrix must contain exactly 2 evaluated items"

    # 4. VERIFY WORKFLOW PAUSED AT HUMAN REVIEW INTERRUPT
    assert retry_res["is_interrupted"] is True
    assert retry_res["current_stage"] == "HUMAN_REVIEW"
    assert retry_res["compliance_score"] == 100.0

    # =========================================================================
    # STEP 5: Resume past Human Review to Final Export
    # =========================================================================
    with patch.object(mcp_client, "get_tool") as mock_export_tool:
        tool = MagicMock()
        tool.invoke.return_value = {
            "success": True,
            "file_path": "/tmp/RFP_Final_Proposal.docx",
            "file_name": "RFP_Final_Proposal.docx"
        }
        mock_export_tool.return_value = tool

        review_res = workflow_manager.resume_human_review(
            project_id=project_id,
            action="APPROVED",
            feedback="All criteria fully met."
        )

    assert review_res["status"] == "COMPLETED"
    final_state = workflow_manager.get_workflow_state(project_id)
    assert final_state["human_review_status"] == "APPROVED"
    assert final_state["export_file_name"] == "RFP_Final_Proposal.docx"
