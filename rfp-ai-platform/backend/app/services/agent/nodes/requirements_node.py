"""
Requirement Analysis Agent Node.
Extracts line-item requirements, submission deadlines, bidder eligibility criteria,
evaluation scoring weights, and mandatory submission attachments.
Strictly isolates infrastructure and LLM quota errors, preventing synthetic error requirements.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState, WorkflowExecutionState
from app.mcp.client import mcp_client


def requirement_analysis_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 2: Requirement Analysis via MCP Tools with error isolation."""
    raw_text = state.get("raw_text", "")
    
    stage_entry = {
        "stage": "REQUIREMENT_ANALYSIS",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    if not raw_text:
        stage_entry["status"] = "FAILED"
        stage_entry["error"] = "Empty raw text from ingestion stage"
        return {
            "execution_state": WorkflowExecutionState.FAILED.value,
            "current_stage": "REQUIREMENT_ANALYSIS",
            "workflow_status": "REQUIREMENT_ANALYSIS_FAILED",
            "blocked_reason": "No document text available for requirement analysis.",
            "retry_stage": "DOCUMENT_INGESTION",
            "requirements": [],
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + ["No document text available for requirement analysis"]
        }
        
    # 1. Extract Requirements
    req_tool = mcp_client.get_tool("extract_rfp_requirements")
    raw_requirements = None
    extraction_error = None
    
    try:
        if req_tool:
            raw_requirements = req_tool.invoke({"text": raw_text})
    except Exception as e:
        extraction_error = str(e)
        
    # Check if tool wrapper returned an error dict
    if isinstance(raw_requirements, dict) and (raw_requirements.get("error") or not raw_requirements.get("success", True)):
        extraction_error = raw_requirements.get("error", "Requirement extraction tool failed")
        raw_requirements = []
        
    # Check if extraction was blocked by quota or infrastructure failure
    if extraction_error:
        is_quota = any(q in extraction_error.lower() for q in ["429", "resource_exhausted", "quota", "rate limit", "exceeded your current quota"])
        is_billing = any(b in extraction_error.lower() for b in ["403", "permission_denied", "free tier is not available", "billing"])
        is_blocked = is_quota or is_billing
        execution_state = WorkflowExecutionState.BLOCKED.value if is_blocked else WorkflowExecutionState.FAILED.value
        status_name = "BLOCKED" if is_blocked else "FAILED"
        
        if is_quota:
            reason = (
                "Google Gemini API Quota Exhausted (HTTP 429 RESOURCE_EXHAUSTED). "
                "Requirement extraction is paused. Please retry once your quota window resets or billing is updated."
            )
        elif is_billing:
            reason = (
                "Google Gemini API Project Restriction (HTTP 403 PERMISSION_DENIED). "
                "The Gemini API free tier is not enabled for this Google Cloud project. "
                "Please configure a valid key from Google AI Studio with free tier access or enable billing at https://aistudio.google.com/billing."
            )
        else:
            reason = f"Requirement extraction failed: {extraction_error}"
        
        stage_entry["status"] = status_name
        stage_entry["error"] = reason
        
        return {
            "execution_state": execution_state,
            "current_stage": "REQUIREMENT_ANALYSIS",
            "workflow_status": f"REQUIREMENT_ANALYSIS_{status_name}",
            "blocked_reason": reason,
            "retry_stage": "REQUIREMENT_ANALYSIS",
            "requirements": [], # NEVER create synthetic requirements!
            "deadlines": [],
            "eligibility_criteria": [],
            "evaluation_criteria": [],
            "mandatory_documents": [],
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + [reason],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
    # Sanitize requirements: discard any synthetic or malformed items
    valid_requirements = []
    if isinstance(raw_requirements, list):
        for r in raw_requirements:
            if isinstance(r, dict) and not str(r.get("requirement_id", "")).startswith("ERR-") and "error" not in str(r.get("requirement_id", "")).lower():
                valid_requirements.append(r)
                
    # 2. Extract Deadlines safely
    deadline_tool = mcp_client.get_tool("extract_deadlines")
    raw_deadlines = deadline_tool.invoke({"text": raw_text}) if deadline_tool else []
    deadlines = [d for d in raw_deadlines if isinstance(d, dict) and not d.get("error")] if isinstance(raw_deadlines, list) else []
    
    # 3. Extract Eligibility safely
    elig_tool = mcp_client.get_tool("extract_eligibility_criteria")
    raw_eligibility = elig_tool.invoke({"text": raw_text}) if elig_tool else []
    eligibility = [el for el in raw_eligibility if isinstance(el, dict) and not el.get("error")] if isinstance(raw_eligibility, list) else []
    
    # 4. Extract Evaluation Criteria safely
    eval_tool = mcp_client.get_tool("extract_evaluation_criteria")
    raw_eval = eval_tool.invoke({"text": raw_text}) if eval_tool else []
    eval_criteria = [ev for ev in raw_eval if isinstance(ev, dict) and not ev.get("error")] if isinstance(raw_eval, list) else []
    
    # 5. Extract Mandatory Documents safely
    docs_tool = mcp_client.get_tool("extract_mandatory_documents")
    raw_docs = docs_tool.invoke({"text": raw_text}) if docs_tool else []
    mandatory_docs = [m for m in raw_docs if isinstance(m, dict) and not m.get("error")] if isinstance(raw_docs, list) else []
    
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Identified {len(valid_requirements)} genuine requirements, {len(deadlines)} deadlines, {len(eligibility)} eligibility criteria, and {len(mandatory_docs)} mandatory submission docs."
    
    return {
        "execution_state": WorkflowExecutionState.RUNNING.value,
        "current_stage": "REQUIREMENT_ANALYSIS",
        "requirements": valid_requirements,
        "deadlines": deadlines,
        "eligibility_criteria": eligibility,
        "evaluation_criteria": eval_criteria,
        "mandatory_documents": mandatory_docs,
        "blocked_reason": None,
        "retry_stage": None,
        "workflow_status": "REQUIREMENT_ANALYSIS_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
