"""
Document Ingestion Agent Node.
Accepts an RFP file, extracts text with OCR fallback, and computes basic stats.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState, WorkflowExecutionState
from app.mcp.client import mcp_client


def document_ingestion_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 1: Document Ingestion using the RFP Document MCP Server."""
    file_path = state.get("file_path", "")
    file_type = state.get("file_type", "pdf")
    
    stage_entry = {
        "stage": "DOCUMENT_INGESTION",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    # If raw_text is already pre-populated (e.g. from upstream memory or testing), proceed
    existing_text = state.get("raw_text", "")
    if existing_text and len(existing_text.strip()) > 0:
        stage_entry["status"] = "COMPLETED"
        return {
            "execution_state": WorkflowExecutionState.RUNNING.value,
            "current_stage": "DOCUMENT_INGESTION",
            "workflow_status": "DOCUMENT_INGESTED",
            "raw_text": existing_text,
            "stage_history": state.get("stage_history", []) + [stage_entry]
        }
    
    extract_tool = mcp_client.get_tool("extract_rfp_text")
    if not extract_tool:
        return {
            "execution_state": WorkflowExecutionState.FAILED.value,
            "current_stage": "DOCUMENT_INGESTION",
            "workflow_status": "DOCUMENT_INGESTION_FAILED",
            "blocked_reason": "MCP tool extract_rfp_text not found.",
            "retry_stage": "DOCUMENT_INGESTION",
            "errors": state.get("errors", []) + ["MCP tool extract_rfp_text not found"]
        }
        
    res = extract_tool.invoke({"file_path": file_path, "file_type": file_type})
    
    if not isinstance(res, dict) or not res.get("success", False):
        err = res.get("error", "Extraction failed") if isinstance(res, dict) else "Extraction failed"
        stage_entry["status"] = "FAILED"
        stage_entry["error"] = err
        return {
            "execution_state": WorkflowExecutionState.FAILED.value,
            "current_stage": "DOCUMENT_INGESTION",
            "workflow_status": "DOCUMENT_INGESTION_FAILED",
            "blocked_reason": err,
            "retry_stage": "DOCUMENT_INGESTION",
            "raw_text": "",
            "stage_history": state.get("stage_history", []) + [stage_entry],
            "errors": state.get("errors", []) + [err]
        }
        
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Extracted {res.get('total_pages', 0)} pages ({res.get('char_count', 0)} chars). Needs OCR: {res.get('needs_ocr', False)}"
    
    return {
        "execution_state": WorkflowExecutionState.RUNNING.value,
        "current_stage": "DOCUMENT_INGESTION",
        "raw_text": res.get("text", ""),
        "total_pages": res.get("total_pages", 0),
        "char_count": res.get("char_count", 0),
        "needs_ocr": res.get("needs_ocr", False),
        "blocked_reason": None,
        "retry_stage": None,
        "workflow_status": "DOCUMENT_INGESTION_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
