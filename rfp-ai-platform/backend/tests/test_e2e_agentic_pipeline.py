import os
import uuid
import pytest
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.services.agent.workflow_manager import workflow_manager
from app.services.assistant.copilot_service import copilot_service

# Mock user for authenticated endpoints
mock_user = User(id=uuid.uuid4(), email="agentic_tester@example.com")

def override_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_current_user

client = TestClient(app)

TEST_PROJECT_ID = str(uuid.uuid4())
TEST_DOC_ID = str(uuid.uuid4())


@pytest.fixture(scope="module")
def sample_rfp_file(tmp_path_factory):
    """Generates a genuine sample RFP docx document on disk."""
    temp_dir = tmp_path_factory.mktemp("rfp_test_data")
    file_path = temp_dir / "sample_cloud_rfp.docx"
    
    doc = docx.Document()
    doc.add_heading("Cloud ERP System Request for Proposal (RFP)", 0)
    doc.add_paragraph("Section 1: Technical & Mandatory Requirements")
    doc.add_paragraph("REQ-001: The system must provide 24/7 technical customer support with 99.9% uptime SLA.")
    doc.add_paragraph("REQ-002: The solution must hold active SOC 2 Type II and ISO 27001 security certifications.")
    doc.add_paragraph("REQ-003: The platform must support OAuth 2.0 and SAML single sign-on authentication.")
    doc.add_paragraph("Section 2: Submission Deadlines")
    doc.add_paragraph("All tender submissions must be completed by 2026-12-31 at 5:00 PM EST.")
    doc.save(str(file_path))
    
    return str(file_path)


def test_full_agentic_workflow_end_to_end(sample_rfp_file):
    """
    Validates end-to-end execution of the 9-stage LangGraph workflow:
    1. Workflow runs through stages 1 to 7 and interrupts before HUMAN_REVIEW (Stage 8)
    2. Checkpointed state contains parsed requirements, retrieved evidence, compliance matrix, and proposal draft
    3. User review is submitted (Human-in-the-loop)
    4. Workflow resumes past checkpoint and finishes EXPORT (Stage 9), generating DOCX
    """
    # 1. Start workflow
    start_result = workflow_manager.start_workflow(
        project_id=TEST_PROJECT_ID,
        document_id=TEST_DOC_ID,
        file_path=sample_rfp_file,
        file_type="docx"
    )
    
    assert start_result is not None
    assert start_result["project_id"] == TEST_PROJECT_ID
    assert start_result.get("is_interrupted") is True
    assert start_result.get("current_stage") == "HUMAN_REVIEW"
    
    # 2. Inspect state at interrupt
    state = workflow_manager.get_workflow_state(TEST_PROJECT_ID)
    assert state is not None
    print("\nSTAGE_HISTORY:", state.get("stage_history"))
    print("ERRORS:", state.get("errors"))
    
    # Verify stages in history
    stage_names = [s.get("stage") for s in state.get("stage_history", [])]
    assert "DOCUMENT_INGESTION" in stage_names
    assert "REQUIREMENT_ANALYSIS" in stage_names
    assert any("KNOWLEDGE_RETRIEVAL" in s for s in stage_names)
    assert "COMPLIANCE_ANALYSIS" in stage_names
    assert any("GAP_ANALYSIS" in s for s in stage_names)
    assert any("PROPOSAL_GENERATION" in s for s in stage_names)
    assert any("PROPOSAL_VALIDATION" in s for s in stage_names)
    
    # Verify strict status types in compliance matrix
    comp_matrix = state.get("compliance_matrix", [])
    assert len(comp_matrix) > 0, "Compliance matrix should contain evaluated items"
    valid_statuses = {"Compliant", "Partially compliant", "Non-compliant", "Requires clarification"}
    for item in comp_matrix:
        assert item["status"] in valid_statuses
        assert "evidence_citations" in item
    
    # Check compliance score is calculated
    metrics = state.get("compliance_score_metrics", {})
    assert "overall_score" in metrics
    assert 0 <= metrics["overall_score"] <= 100
    
    # Check proposal draft sections
    sections = state.get("draft_sections", [])
    assert len(sections) >= 3
    section_titles = [s.get("section_name", s.get("title", "")) for s in sections]
    assert any("Executive Summary" in t for t in section_titles)
    assert any("Technical" in t for t in section_titles)
    
    # Check QA validation results
    validation = state.get("validation_results", {})
    assert "is_valid" in validation
    
    # 3. Resume workflow via Human-in-the-loop review
    resume_result = workflow_manager.resume_human_review(
        project_id=TEST_PROJECT_ID,
        action="APPROVED",
        feedback="Executive summary and technical requirements approved for final export."
    )
    
    assert resume_result is not None
    assert resume_result.get("status") in ["COMPLETED", "APPROVED"]
    
    # 4. Verify export package
    export_path = resume_result.get("export_file_path")
    assert export_path is not None
    assert os.path.exists(export_path)
    assert os.path.getsize(export_path) > 0
    assert export_path.endswith(".docx")


def test_workflow_api_status_and_compliance():
    """
    Validates REST API endpoints for workflow status, compliance inspection, and proposal review.
    """
    # 1. Poll Status
    status_res = client.get(f"/api/workflow/{TEST_PROJECT_ID}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["project_id"] == TEST_PROJECT_ID
    assert "compliance_score" in status_data
    assert "stage_history" in status_data
    
    # 2. Get Compliance Report
    comp_res = client.get(f"/api/workflow/{TEST_PROJECT_ID}/compliance")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "compliance_matrix" in comp_data
    assert "metrics" in comp_data
    assert len(comp_data["compliance_matrix"]) > 0
    
    # 3. Get Proposal Draft
    prop_res = client.get(f"/api/workflow/{TEST_PROJECT_ID}/proposal")
    assert prop_res.status_code == 200
    prop_data = prop_res.json()
    assert "sections" in prop_data
    assert len(prop_data["sections"]) >= 3
    
    # 4. Submit Human Review via API (Test Revision loop)
    review_res = client.post(f"/api/workflow/{TEST_PROJECT_ID}/review", json={
        "action": "APPROVED",
        "feedback": "All sections are verified."
    })
    assert review_res.status_code == 200
    assert review_res.json().get("status") in ["COMPLETED", "APPROVED"]


def test_copilot_assistant_chat_and_history():
    """
    Validates AI Copilot chat interaction, multi-turn history, and citations.
    """
    # 1. Ask Copilot about requirements and compliance for the analyzed project
    chat_res = client.post("/api/assistant/chat", json={
        "project_id": TEST_PROJECT_ID,
        "message": "What is our compliance score and what certifications do we have?"
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert len(chat_data["answer"]) > 0
    assert "citations" in chat_data
    assert "suggested_followups" in chat_data
    assert len(chat_data["suggested_followups"]) > 0
    
    # 2. Verify history endpoint
    history_res = client.get(f"/api/assistant/{TEST_PROJECT_ID}/history")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data.get("history", [])) >= 2
    
    # 3. Clear history
    del_res = client.delete(f"/api/assistant/{TEST_PROJECT_ID}/history")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
