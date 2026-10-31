"""
Proposal Generation Agent Node.
Drafts full proposal sections and requirement responses grounded in verified evidence.
Incorporates revision feedback on iterative cycles.
"""

from datetime import datetime, timezone
from app.services.agent.state import RFPWorkflowState
from app.mcp.client import mcp_client


def proposal_generation_node(state: RFPWorkflowState) -> dict:
    """Executes Stage 6: Proposal Generation via Proposal MCP Server."""
    project_id = state.get("project_id", "default")
    requirements = state.get("requirements", [])
    evidence_map = state.get("retrieved_evidence", {})
    iteration = state.get("generation_iterations", 0) + 1
    
    val_results = state.get("validation_results", {})
    human_feedback = state.get("human_feedback")
    critique = human_feedback or val_results.get("critique", "")
    
    stage_entry = {
        "stage": f"PROPOSAL_GENERATION_CYCLE_{iteration}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS"
    }
    
    gen_tool = mcp_client.get_tool("generate_proposal_section")
    rev_tool = mcp_client.get_tool("revise_proposal_section")
    save_tool = mcp_client.get_tool("save_proposal_draft")
    
    all_chunks = []
    for c_list in evidence_map.values():
        all_chunks.extend(c_list)
        
    sections = []
    draft_responses = dict(state.get("draft_responses", {}))
    
    # 1. Executive Summary Section
    if iteration > 1 and critique and rev_tool:
        # Revision mode
        old_content = next((s.get("content") for s in state.get("draft_sections", []) if s.get("section_name") == "Executive Summary"), "")
        rev = rev_tool.invoke({
            "section_text": old_content,
            "critique": critique,
            "additional_evidence": all_chunks[:5]
        })
        exec_content = rev.get("revised_content", old_content)
    else:
        # Initial generation mode
        exec_res = gen_tool.invoke({
            "section_name": "Executive Summary & Solution Overview",
            "requirements": requirements,
            "evidence_chunks": all_chunks
        }) if gen_tool else {}
        exec_content = exec_res.get("content", "Executive Summary")
        
    sections.append({
        "section_name": "Executive Summary & Solution Overview",
        "title": "Executive Summary & Solution Overview",
        "content": exec_content
    })
    if save_tool:
        save_tool.invoke({"project_id": project_id, "section_name": "Executive_Summary", "content": exec_content})
        
    # 2. Technical Architecture Section
    tech_reqs = [r for r in requirements if isinstance(r, dict) and r.get("category") in ["Technical", "Functional", "Infrastructure"]] or requirements
    tech_res = gen_tool.invoke({
        "section_name": "Technical Architecture & Operational Approach",
        "requirements": tech_reqs,
        "evidence_chunks": all_chunks
    }) if gen_tool else {}
    tech_content = tech_res.get("content", "Technical Architecture Details") if isinstance(tech_res, dict) else str(tech_res)
    sections.append({
        "section_name": "Technical Architecture & Operational Approach",
        "title": "Technical Architecture & Operational Approach",
        "content": tech_content
    })
    if save_tool:
        save_tool.invoke({"project_id": project_id, "section_name": "Technical_Architecture", "content": tech_content})
        
    # 3. Security, Privacy & Compliance Section
    sec_reqs = [r for r in requirements if isinstance(r, dict) and r.get("category") in ["Security", "Compliance", "Legal"]] or requirements
    sec_res = gen_tool.invoke({
        "section_name": "Security, Compliance & SLA Commitments",
        "requirements": sec_reqs,
        "evidence_chunks": all_chunks
    }) if gen_tool else {}
    sec_content = sec_res.get("content", "Security and Compliance Commitments") if isinstance(sec_res, dict) else str(sec_res)
    sections.append({
        "section_name": "Security, Compliance & SLA Commitments",
        "title": "Security, Compliance & SLA Commitments",
        "content": sec_content
    })
    if save_tool:
        save_tool.invoke({"project_id": project_id, "section_name": "Security_and_SLAs", "content": sec_content})

    # 4. Implementation Plan & Governance
    imp_res = gen_tool.invoke({
        "section_name": "Implementation Roadmap & Team Qualifications",
        "requirements": requirements,
        "evidence_chunks": all_chunks
    }) if gen_tool else {}
    imp_content = imp_res.get("content", "Implementation Roadmap and Professional Services Team Qualifications") if isinstance(imp_res, dict) else str(imp_res)
    sections.append({
        "section_name": "Implementation Roadmap & Team Qualifications",
        "title": "Implementation Roadmap & Team Qualifications",
        "content": imp_content
    })
    if save_tool:
        save_tool.invoke({"project_id": project_id, "section_name": "Implementation_Roadmap", "content": imp_content})
        
    # 4. Generate per-requirement responses for the compliance matrix
    for req in requirements:
        req_id = req.get("requirement_id")
        desc = req.get("description", "")
        req_chunks = evidence_map.get(req_id, [])
        if req_chunks:
            chunk_texts = " ".join([c.get("text", "") for c in req_chunks[:2]])
            draft_responses[req_id] = f"Our solution meets this requirement in full. {chunk_texts[:350]}..."
        else:
            draft_responses[req_id] = "Insufficient evidence in the knowledge base."
            
    stage_entry["status"] = "COMPLETED"
    stage_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    stage_entry["summary"] = f"Drafted 3 comprehensive proposal sections and {len(draft_responses)} requirement line-item responses."
    
    return {
        "draft_sections": sections,
        "draft_responses": draft_responses,
        "generation_iterations": iteration,
        "human_feedback": None, # Clear processed feedback
        "workflow_status": "PROPOSAL_GENERATION_COMPLETE",
        "stage_history": state.get("stage_history", []) + [stage_entry],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
