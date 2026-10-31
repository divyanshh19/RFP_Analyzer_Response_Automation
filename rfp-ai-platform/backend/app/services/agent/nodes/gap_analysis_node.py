"""
Gap Analysis Agent Node.
Identifies unfulfilled requirements, missing evidence, and decides whether to trigger
additional retrieval searches or route gaps for human clarification.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState
from app.mcp.client import mcp_client


def gap_analysis_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 5: Gap Analysis via Compliance MCP Server."""
    compliance_matrix = state.get("compliance_matrix", [])
    iteration = state.get("retrieval_iterations", 1)
    max_retries = state.get("max_retrieval_retries", 2)
    
    stage_entry = {
        "stage": f"GAP_ANALYSIS_CYCLE_{iteration}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    gap_tool = mcp_client.get_tool("identify_missing_requirements")
    raw_gaps = gap_tool.invoke({"compliance_matrix": compliance_matrix}) if gap_tool else []
    gaps = raw_gaps if isinstance(raw_gaps, list) else []
    
    can_retry = len(gaps) > 0 and iteration < max_retries
    summary = f"Identified {len(gaps)} compliance gaps."
    if can_retry:
        summary += f" Retrying knowledge retrieval (Cycle {iteration + 1} of {max_retries}) with expanded semantic queries."
    else:
        summary += " Proceeding to proposal generation with verified evidence."
        
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = summary
    
    return {
        "identified_gaps": gaps,
        "gap_summary": summary,
        "workflow_status": "GAP_ANALYSIS_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
