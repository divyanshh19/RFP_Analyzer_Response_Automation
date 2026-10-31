"""
Knowledge Retrieval Agent Node.
Gathers verified evidence chunks for each requirement from the enterprise knowledge base.
Supports iterative re-retrieval targeting identified gaps.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any
from app.services.agent.state import RFPWorkflowState
from app.mcp.client import mcp_client


def knowledge_retrieval_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 3: Knowledge Retrieval via Knowledge Base MCP Server."""
    requirements = state.get("requirements", [])
    current_evidence = dict(state.get("retrieved_evidence", {}))
    iteration = state.get("retrieval_iterations", 0) + 1
    gaps = state.get("identified_gaps", [])
    
    stage_entry = {
        "stage": f"KNOWLEDGE_RETRIEVAL_CYCLE_{iteration}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    evidence_tool = mcp_client.get_tool("search_supporting_evidence")
    cap_tool = mcp_client.get_tool("retrieve_company_capabilities")
    cert_tool = mcp_client.get_tool("retrieve_certifications")
    
    # If in retry cycle, only retrieve for requirements identified as gaps
    target_reqs = requirements if isinstance(requirements, list) else []
    if iteration > 1 and gaps and isinstance(gaps, list):
        gap_ids = {g.get("requirement_id") for g in gaps if isinstance(g, dict) and g.get("requirement_id")}
        if gap_ids:
            target_reqs = [r for r in target_reqs if isinstance(r, dict) and r.get("requirement_id") in gap_ids]
        
    for req in target_reqs:
        if not isinstance(req, dict):
            continue
        req_id = req.get("requirement_id")
        desc = req.get("description", "")
        category = req.get("category", "")
        
        # 1. Direct requirement evidence search
        chunks = []
        if evidence_tool:
            chunks.extend(evidence_tool.invoke({"requirement_text": desc, "top_k": 4}))
            
        # 2. Targeted category / certification augmentation
        if "certif" in desc.lower() or "iso" in desc.lower() or "soc" in desc.lower():
            if cert_tool:
                cert_chunks = cert_tool.invoke({"certification_name": desc, "top_k": 3})
                chunks.extend(cert_chunks)
        elif category and cap_tool:
            cap_chunks = cap_tool.invoke({"domain": category, "top_k": 2})
            chunks.extend(cap_chunks)
            
        # Deduplicate chunks by chunk_id
        seen_ids = set()
        deduped = []
        for c in chunks:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids and cid != "ERR":
                seen_ids.add(cid)
                deduped.append(c)
                
        # Merge or update
        current_evidence[req_id] = deduped
        
    total_chunks_found = sum(len(c) for c in current_evidence.values())
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Cycle {iteration}: Retrieved evidence for {len(target_reqs)} requirements. Total active citations: {total_chunks_found} chunks."
    
    return {
        "retrieved_evidence": current_evidence,
        "retrieval_iterations": iteration,
        "workflow_status": "KNOWLEDGE_RETRIEVAL_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
