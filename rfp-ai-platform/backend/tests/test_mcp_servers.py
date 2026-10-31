"""
Unit and Integration Tests for MCP Servers:
- RFP Document Server
- Knowledge Base Server
- Compliance Server
- Proposal Server
"""

import os
import sys
import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.mcp.rfp_document_server import mcp as doc_mcp
from app.mcp.knowledge_base_server import mcp as kb_mcp
from app.mcp.compliance_server import mcp as comp_mcp, calculate_compliance_score, identify_missing_requirements, ComplianceStatus
from app.mcp.proposal_server import mcp as prop_mcp, export_proposal


def test_mcp_servers_tool_registration():
    """Verify that all custom MCP servers properly register their tools."""
    # 1. Document Server Tools
    doc_tools = [t.name for t in doc_mcp._tool_manager.list_tools()]
    assert "extract_rfp_text" in doc_tools
    assert "extract_rfp_requirements" in doc_tools
    assert "extract_deadlines" in doc_tools
    assert "extract_eligibility_criteria" in doc_tools
    assert "extract_evaluation_criteria" in doc_tools
    assert "extract_mandatory_documents" in doc_tools
    
    # 2. Knowledge Base Server Tools
    kb_tools = [t.name for t in kb_mcp._tool_manager.list_tools()]
    assert "search_company_documents" in kb_tools
    assert "retrieve_company_capabilities" in kb_tools
    assert "retrieve_certifications" in kb_tools
    assert "retrieve_relevant_experience" in kb_tools
    assert "search_supporting_evidence" in kb_tools
    
    # 3. Compliance Server Tools
    comp_tools = [t.name for t in comp_mcp._tool_manager.list_tools()]
    assert "map_requirements_to_capabilities" in comp_tools
    assert "identify_missing_requirements" in comp_tools
    assert "calculate_compliance_score" in comp_tools
    assert "validate_response_coverage" in comp_tools
    assert "retrieve_requirement_evidence" in comp_tools
    
    # 4. Proposal Server Tools
    prop_tools = [t.name for t in prop_mcp._tool_manager.list_tools()]
    assert "generate_proposal_section" in prop_tools
    assert "validate_proposal_content" in prop_tools
    assert "revise_proposal_section" in prop_tools
    assert "save_proposal_draft" in prop_tools
    assert "export_proposal" in prop_tools


def test_compliance_score_calculation():
    """Verify objective evidence-based compliance score calculations."""
    mock_matrix = [
        {
            "requirement_id": "REQ-001",
            "description": "24/7 technical support required.",
            "status": ComplianceStatus.COMPLIANT,
            "compliance_score": 1.0,
            "mandatory": True
        },
        {
            "requirement_id": "REQ-002",
            "description": "SOC 2 Type II certification required.",
            "status": ComplianceStatus.PARTIALLY_COMPLIANT,
            "compliance_score": 0.5,
            "mandatory": True
        },
        {
            "requirement_id": "REQ-003",
            "description": "ISO 27001 certification required.",
            "status": ComplianceStatus.NON_COMPLIANT,
            "compliance_score": 0.0,
            "mandatory": True
        },
        {
            "requirement_id": "REQ-004",
            "description": "Custom API integration timeline.",
            "status": ComplianceStatus.REQUIRES_CLARIFICATION,
            "compliance_score": 0.5,
            "mandatory": False
        }
    ]
    
    result = calculate_compliance_score(mock_matrix)
    
    # Overall score = (1.0 + 0.5 + 0.0 + 0.5) / 4 = 2.0 / 4 = 50.0%
    assert result["overall_score"] == 50.0
    assert result["total_requirements"] == 4
    assert result["compliant_count"] == 1
    assert result["partially_compliant_count"] == 1
    assert result["non_compliant_count"] == 1
    assert result["clarification_count"] == 1
    # Mandatory items: REQ-001, REQ-002, REQ-003 => (1.0 + 0.5 + 0.0) / 3 = 1.5 / 3 = 50.0%
    assert result["mandatory_compliance_score"] == 50.0


def test_identify_missing_requirements_gap_analysis():
    """Verify that non-compliant and clarification-required items are accurately flagged as gaps."""
    mock_matrix = [
        {"requirement_id": "REQ-001", "status": ComplianceStatus.COMPLIANT, "description": "OK"},
        {"requirement_id": "REQ-002", "status": ComplianceStatus.NON_COMPLIANT, "description": "Missing SOC 2", "missing_information": "SOC 2 Type II report"},
        {"requirement_id": "REQ-003", "status": ComplianceStatus.REQUIRES_CLARIFICATION, "description": "Ambiguous SLA", "missing_information": "Clarify MTTR SLA"}
    ]
    
    gaps = identify_missing_requirements(mock_matrix)
    assert len(gaps) == 2
    gap_ids = [g["requirement_id"] for g in gaps]
    assert "REQ-002" in gap_ids
    assert "REQ-003" in gap_ids
    assert "REQ-001" not in gap_ids


def test_proposal_export_docx(tmp_path):
    """Verify that export_proposal compiles a valid Microsoft Word .docx document."""
    project_id = "test-project-123"
    title = "Technical Tender Bid Submission"
    sections = [
        {"section_name": "Executive Summary", "content": "NovaCare provides enterprise-grade healthcare cloud software."},
        {"section_name": "Technical Architecture", "content": "Our solution is built on microservices with 99.99% availability."}
    ]
    compliance_matrix = [
        {"requirement_id": "REQ-001", "description": "24/7 Support", "status": "Compliant", "rationale": "Directly evidenced in company profile."}
    ]
    
    result = export_proposal(project_id, title, sections, compliance_matrix)
    assert result["success"] is True
    assert os.path.exists(result["file_path"])
    assert result["file_path"].endswith(".docx")
    
    # Clean up generated test docx
    try:
        os.remove(result["file_path"])
    except Exception:
        pass
