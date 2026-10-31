"""
Export Agent Node.
Compiles the approved proposal draft and compliance matrix into a branded Microsoft Word (.docx) document.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState
from app.mcp.client import mcp_client


def export_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 9: Proposal Export via Proposal MCP Server."""
    project_id = state.get("project_id", "default")
    sections = state.get("draft_sections", [])
    compliance_matrix = state.get("compliance_matrix", [])
    
    stage_entry = {
        "stage": "EXPORT",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    export_tool = mcp_client.get_tool("export_proposal")
    if not export_tool:
        stage_entry["status"] = "FAILED"
        return {
            "workflow_status": "FAILED",
            "errors": state.get("errors", []) + ["MCP export_proposal tool not found"]
        }
        
    title = f"RFP Proposal Response - Project {project_id}"
    res = export_tool.invoke({
        "project_id": project_id,
        "title": title,
        "sections": sections,
        "compliance_matrix": compliance_matrix
    })
    
    if not res.get("success", False):
        stage_entry["status"] = "FAILED"
        stage_entry["error"] = res.get("error", "Export compilation failed")
        return {
            "workflow_status": "FAILED",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + [res.get("error", "Export compilation failed")]
        }
        
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Generated final Word document package: {res.get('file_name')} at {res.get('file_path')}."
    
    return {
        "export_file_path": res.get("file_path"),
        "export_file_name": res.get("file_name"),
        "workflow_status": "COMPLETED",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
