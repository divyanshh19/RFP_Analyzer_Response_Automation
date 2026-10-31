"""
Compliance Analysis Agent Node.
Maps retrieved evidence to individual requirements and computes objective compliance metrics.
Strictly isolates infrastructure and quota errors, preventing synthetic error rows or fabricated scores.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState, WorkflowExecutionState
from app.mcp.client import mcp_client


def compliance_analysis_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 4: Compliance Analysis via Compliance MCP Server with strict error isolation."""
    requirements = state.get("requirements", [])
    evidence_map = state.get("retrieved_evidence", {})
    
    stage_entry = {
        "stage": "COMPLIANCE_ANALYSIS",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    # If no requirements were extracted, do not fabricate compliance results
    if not requirements:
        stage_entry["status"] = "FAILED"
        stage_entry["error"] = "No requirements available for compliance analysis."
        return {
            "execution_state": state.get("execution_state", WorkflowExecutionState.FAILED.value),
            "current_stage": "COMPLIANCE_ANALYSIS",
            "workflow_status": "COMPLIANCE_ANALYSIS_FAILED",
            "blocked_reason": state.get("blocked_reason") or "No requirements available to evaluate.",
            "retry_stage": "REQUIREMENT_ANALYSIS",
            "compliance_matrix": [],
            "compliance_score_metrics": {
                "overall_score": None,
                "mandatory_compliance_score": None,
                "total_requirements": 0,
                "is_valid": False,
                "audit_summary": "No requirements available to assess."
            },
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + ["No requirements available to assess"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
    map_tool = mcp_client.get_tool("map_requirements_to_capabilities")
    score_tool = mcp_client.get_tool("calculate_compliance_score")
    
    if not map_tool or not score_tool:
        return {
            "execution_state": WorkflowExecutionState.FAILED.value,
            "current_stage": "COMPLIANCE_ANALYSIS",
            "workflow_status": "FAILED",
            "blocked_reason": "Compliance MCP tools not found.",
            "retry_stage": "COMPLIANCE_ANALYSIS",
            "compliance_matrix": [],
            "compliance_score_metrics": {"overall_score": None, "mandatory_compliance_score": None, "is_valid": False},
            "errors": state.get("errors", []) + ["Compliance MCP tools not found"]
        }
        
    raw_matrix = None
    mapping_error = None
    try:
        raw_matrix = map_tool.invoke({
            "requirements": requirements,
            "evidence_map": evidence_map
        })
    except Exception as e:
        mapping_error = str(e)
        
    # Check if tool wrapper returned an error
    if isinstance(raw_matrix, dict) and (raw_matrix.get("error") or not raw_matrix.get("success", True)):
        mapping_error = raw_matrix.get("error", "Compliance mapping tool failed")
        raw_matrix = []
        
    if mapping_error:
        is_quota = any(q in mapping_error.lower() for q in ["429", "resource_exhausted", "quota", "rate limit", "exceeded your current quota"])
        is_billing = any(b in mapping_error.lower() for b in ["403", "permission_denied", "free tier is not available", "billing"])
        is_blocked = is_quota or is_billing
        execution_state = WorkflowExecutionState.BLOCKED.value if is_blocked else WorkflowExecutionState.FAILED.value
        status_name = "BLOCKED" if is_blocked else "FAILED"
        
        if is_quota:
            reason = (
                "Google Gemini API Quota Exhausted (HTTP 429 RESOURCE_EXHAUSTED) during compliance analysis. "
                "Assessment paused. Please retry once your quota window resets."
            )
        elif is_billing:
            reason = (
                "Google Gemini API Project Restriction (HTTP 403 PERMISSION_DENIED) during compliance analysis. "
                "Please configure an API key with active tier access or enable billing at https://aistudio.google.com/billing."
            )
        else:
            reason = f"Compliance analysis failed: {mapping_error}"
        
        stage_entry["status"] = status_name
        stage_entry["error"] = reason
        
        return {
            "execution_state": execution_state,
            "current_stage": "COMPLIANCE_ANALYSIS",
            "workflow_status": f"COMPLIANCE_ANALYSIS_{status_name}",
            "blocked_reason": reason,
            "retry_stage": "COMPLIANCE_ANALYSIS",
            "compliance_matrix": [], # Never fabricate items!
            "compliance_score_metrics": {
                "overall_score": None,
                "mandatory_compliance_score": None,
                "total_requirements": len(requirements),
                "is_valid": False,
                "audit_summary": "Assessment blocked by API error."
            },
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + [reason],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
    compliance_matrix = raw_matrix if isinstance(raw_matrix, list) else []
    
    raw_metrics = score_tool.invoke({
        "compliance_matrix": compliance_matrix
    })
    metrics = raw_metrics if isinstance(raw_metrics, dict) else {
        "overall_score": None,
        "mandatory_compliance_score": None,
        "total_requirements": len(compliance_matrix),
        "is_valid": False
    }
    
    score_display = f"{metrics.get('overall_score')}%" if metrics.get("overall_score") is not None else "N/A"
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Calculated Compliance Score: {score_display}. ({metrics.get('audit_summary', '')})"
    
    return {
        "execution_state": WorkflowExecutionState.RUNNING.value,
        "current_stage": "COMPLIANCE_ANALYSIS",
        "compliance_matrix": compliance_matrix,
        "compliance_score_metrics": metrics,
        "blocked_reason": None,
        "retry_stage": None,
        "workflow_status": "COMPLIANCE_ANALYSIS_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
