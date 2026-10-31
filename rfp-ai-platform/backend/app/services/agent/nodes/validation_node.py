"""
Proposal Validation Agent Node.
Performs automated QA on drafted proposal sections, verifying evidence traceability
and checking for requirement coverage before human review.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState
from app.mcp.client import mcp_client


def proposal_validation_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 7: Proposal Validation via Proposal and Compliance MCP Servers."""
    sections = state.get("draft_sections", [])
    requirements = state.get("requirements", [])
    evidence_map = state.get("retrieved_evidence", {})
    draft_responses = state.get("draft_responses", {})
    iteration = state.get("generation_iterations", 1)
    
    stage_entry = {
        "stage": f"PROPOSAL_VALIDATION_CYCLE_{iteration}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    val_tool = mcp_client.get_tool("validate_proposal_content")
    cov_tool = mcp_client.get_tool("validate_response_coverage")
    
    all_chunks = []
    for c_list in evidence_map.values():
        all_chunks.extend(c_list)
        
    unsupported_claims = []
    critiques = []
    is_valid = True
    
    # 1. Validate content of each section
    if val_tool and sections:
        for sec in sections:
            res = val_tool.invoke({
                "section_text": sec.get("content", ""),
                "evidence_chunks": all_chunks,
                "requirements": requirements
            })
            if isinstance(res, dict) and not res.get("is_valid", True):
                is_valid = False
                unsupported_claims.extend(res.get("unsupported_claims", []))
                critiques.append(f"[{sec.get('section_name')}]: {res.get('critique', '')}")
                
    # 2. Check coverage
    coverage_result = {}
    if cov_tool:
        raw_cov = cov_tool.invoke({
            "requirements": requirements,
            "responses": draft_responses
        })
        coverage_result = raw_cov if isinstance(raw_cov, dict) else {}
        if not coverage_result.get("is_complete", True):
            missing_ids = coverage_result.get("missing_req_ids", [])
            critiques.append(f"Incomplete coverage: {len(missing_ids)} requirements lack sufficient evidence ({', '.join(missing_ids[:5])}).")
            
    summary_critique = "Proposal validated and compliant with evidence." if is_valid else "; ".join(critiques)
    
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Validation result: {'PASSED' if is_valid else 'REVISION_NEEDED'}. Coverage: {coverage_result.get('coverage_percentage', 100)}%."
    
    return {
        "validation_results": {
            "is_valid": is_valid,
            "unsupported_claims": unsupported_claims,
            "critique": summary_critique,
            "coverage": coverage_result
        },
        "workflow_status": "PROPOSAL_VALIDATION_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
