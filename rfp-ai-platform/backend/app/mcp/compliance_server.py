"""
Compliance MCP Server
Exposes standardized Model Context Protocol (MCP) tools for mapping requirements to capabilities,
calculating evidence-grounded compliance scores, and analyzing missing requirements.
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from google import genai
from google.genai import types

mcp = FastMCP("compliance-server")

def _get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)


class ComplianceStatus:
    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially compliant"
    NON_COMPLIANT = "Non-compliant"
    REQUIRES_CLARIFICATION = "Requires clarification"


@mcp.tool(
    name="map_requirements_to_capabilities",
    description="Evaluate RFP requirements against retrieved knowledge-base evidence chunks. Assigns strict compliance status (Compliant, Partially compliant, Non-compliant, Requires clarification) with rationale and citations."
)
def map_requirements_to_capabilities(
    requirements: List[Dict[str, Any]],
    evidence_map: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Evaluates each requirement against its associated evidence chunks.
    Strictly forbids hallucinating compliance if evidence is missing.
    """
    if not requirements or not isinstance(requirements, list):
        return []
        
    client = _get_gemini_client()
    compliance_results = []
    
    # Process in batches or individually to maintain precision
    for req in requirements:
        if not isinstance(req, dict):
            continue
        req_id = req.get("requirement_id", "REQ-UNKNOWN")
        desc = req.get("description", "")
        category = req.get("category", "General")
        is_mandatory = req.get("mandatory", True)
        
        chunks = evidence_map.get(req_id, []) if isinstance(evidence_map, dict) else []
        if not chunks:
            compliance_results.append({
                "requirement_id": req_id,
                "description": desc,
                "category": category,
                "mandatory": is_mandatory,
                "status": ComplianceStatus.NON_COMPLIANT,
                "compliance_score": 0.0,
                "rationale": "No relevant evidence found in the company knowledge base.",
                "evidence_citations": [],
                "missing_information": "Complete capability evidence missing from repository."
            })
            continue
            
        evidence_context = "\n\n".join([
            f"[Chunk ID: {c.get('chunk_id')}, Page: {c.get('page_number')}, Section: {c.get('section_name')}]\n{c.get('text')}"
            for c in chunks
        ])
        
        prompt = f"""
You are an expert procurement compliance auditor. 
Evaluate whether the following RFP Requirement is supported by the provided Company Evidence.

RFP REQUIREMENT:
ID: {req_id}
Description: {desc}
Category: {category}
Mandatory: {is_mandatory}

COMPANY EVIDENCE:
{evidence_context}

RULES:
1. Status MUST be exactly one of:
   - "Compliant" (Direct, unequivocal evidence in the text proves company fully meets the requirement)
   - "Partially compliant" (Evidence proves company meets part of the requirement, but has gaps)
   - "Non-compliant" (Evidence directly contradicts, or evidence has no mention of the required capability)
   - "Requires clarification" (Evidence is ambiguous, or tender phrasing needs buyer clarification)
2. Score: float between 0.0 (Non-compliant) and 1.0 (Fully compliant).
3. Be rigorous: DO NOT ASSUME OR FABRICATE claims. If the evidence does not state it, it is Non-compliant or Partially compliant.

Return a valid JSON object:
{{
  "status": "Compliant | Partially compliant | Non-compliant | Requires clarification",
  "compliance_score": 0.0 to 1.0,
  "rationale": "Clear 2-sentence explanation of the compliance determination",
  "cited_chunk_ids": ["chunk_id_1"],
  "missing_information": "What specific information or certification is absent, or null if compliant"
}}
"""
        try:
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            item_data = json.loads(resp.text)
            
            # Sanitize status to exact enum
            raw_status = item_data.get("status", "").strip().lower()
            if "partially" in raw_status:
                status = ComplianceStatus.PARTIALLY_COMPLIANT
            elif "non" in raw_status or "not" in raw_status:
                status = ComplianceStatus.NON_COMPLIANT
            elif "clarif" in raw_status:
                status = ComplianceStatus.REQUIRES_CLARIFICATION
            elif "compliant" in raw_status:
                status = ComplianceStatus.COMPLIANT
            else:
                status = ComplianceStatus.REQUIRES_CLARIFICATION
                
            compliance_results.append({
                "requirement_id": req_id,
                "description": desc,
                "category": category,
                "mandatory": is_mandatory,
                "status": status,
                "compliance_score": float(item_data.get("compliance_score", 0.0)),
                "rationale": item_data.get("rationale", ""),
                "evidence_citations": [c for c in chunks if c.get("chunk_id") in item_data.get("cited_chunk_ids", [])] or chunks[:1],
                "missing_information": item_data.get("missing_information")
            })
        except Exception as e:
            # Strictly raise API and quota errors. Never convert infrastructure errors into "Requires Clarification" with 50% score.
            raise RuntimeError(f"Compliance LLM evaluation failed for {req_id}: {str(e)}") from e
            
    return compliance_results


@mcp.tool(
    name="identify_missing_requirements",
    description="Filter compliance matrix for items marked as Non-compliant or Requires clarification to prioritize gap remediation."
)
def identify_missing_requirements(compliance_matrix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identifies all gaps and requirements lacking adequate evidence."""
    if not isinstance(compliance_matrix, list):
        return []
    gaps = []
    for item in compliance_matrix:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_id", "")).startswith("ERR-") or "error" in str(item.get("requirement_id", "")).lower():
            continue
        status = item.get("status")
        if status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.REQUIRES_CLARIFICATION, ComplianceStatus.PARTIALLY_COMPLIANT]:
            gaps.append({
                "requirement_id": item.get("requirement_id"),
                "description": item.get("description"),
                "category": item.get("category"),
                "mandatory": item.get("mandatory", True),
                "status": status,
                "missing_information": item.get("missing_information") or item.get("rationale"),
                "suggested_action": "Search additional company archives or request human SME clarification"
            })
    return gaps


@mcp.tool(
    name="calculate_compliance_score",
    description="Calculate aggregate objective compliance metrics (overall score 0-100%, breakdown of compliant, partial, non-compliant, and clarification-required counts)."
)
def calculate_compliance_score(compliance_matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes evidence-grounded aggregate compliance score."""
    if not isinstance(compliance_matrix, list) or not compliance_matrix:
        return {
            "overall_score": None,
            "total_requirements": 0,
            "compliant_count": 0,
            "partially_compliant_count": 0,
            "non_compliant_count": 0,
            "clarification_count": 0,
            "mandatory_compliance_score": None,
            "is_valid": False,
            "audit_summary": "No valid compliance assessment exists."
        }
        
    # Strictly filter for genuine evaluated RFP requirements. Never include synthetic errors.
    valid_items = [
        i for i in compliance_matrix 
        if isinstance(i, dict) 
        and not str(i.get("requirement_id", "")).startswith("ERR-")
        and "error" not in str(i.get("requirement_id", "")).lower()
        and i.get("status") in [
            ComplianceStatus.COMPLIANT,
            ComplianceStatus.PARTIALLY_COMPLIANT,
            ComplianceStatus.NON_COMPLIANT,
            ComplianceStatus.REQUIRES_CLARIFICATION
        ]
    ]
    total = len(valid_items)
    if total == 0:
        return {
            "overall_score": None,
            "total_requirements": 0,
            "compliant_count": 0,
            "partially_compliant_count": 0,
            "non_compliant_count": 0,
            "clarification_count": 0,
            "mandatory_compliance_score": None,
            "is_valid": False,
            "audit_summary": "No valid compliance assessment exists."
        }
        
    compliant = 0
    partial = 0
    non_compliant = 0
    clarification = 0
    
    total_score_sum = 0.0
    mandatory_total = 0
    mandatory_score_sum = 0.0
    
    for item in valid_items:
        status = item.get("status")
        score = float(item.get("compliance_score", 0.0))
        is_mand = item.get("mandatory", True)
        
        total_score_sum += score
        if is_mand:
            mandatory_total += 1
            mandatory_score_sum += score
            
        if status == ComplianceStatus.COMPLIANT:
            compliant += 1
        elif status == ComplianceStatus.PARTIALLY_COMPLIANT:
            partial += 1
        elif status == ComplianceStatus.NON_COMPLIANT:
            non_compliant += 1
        else:
            clarification += 1
            
    overall_percentage = round((total_score_sum / total) * 100.0, 1)
    mand_percentage = round((mandatory_score_sum / mandatory_total) * 100.0, 1) if mandatory_total > 0 else 100.0
    
    return {
        "overall_score": overall_percentage,
        "total_requirements": total,
        "compliant_count": compliant,
        "partially_compliant_count": partial,
        "non_compliant_count": non_compliant,
        "clarification_count": clarification,
        "mandatory_compliance_score": mand_percentage,
        "is_valid": True,
        "audit_summary": f"{compliant} Compliant, {partial} Partially Compliant, {non_compliant} Non-Compliant, {clarification} Need Clarification out of {total} requirements."
    }


@mcp.tool(
    name="validate_response_coverage",
    description="Check whether every extracted requirement has a corresponding drafted proposal response."
)
def validate_response_coverage(
    requirements: List[Dict[str, Any]],
    responses: Dict[str, str]
) -> Dict[str, Any]:
    """Validates that all requirements have draft responses and checks for empty responses."""
    total = len(requirements)
    if total == 0:
        return {"covered_count": 0, "missing_count": 0, "coverage_percentage": 100.0, "missing_req_ids": []}
        
    missing = []
    covered = 0
    for req in requirements:
        req_id = req.get("requirement_id")
        resp_text = responses.get(req_id, "").strip()
        if not resp_text or "insufficient evidence" in resp_text.lower():
            missing.append(req_id)
        else:
            covered += 1
            
    coverage_pct = round((covered / total) * 100.0, 1)
    return {
        "total_requirements": total,
        "covered_count": covered,
        "missing_count": len(missing),
        "coverage_percentage": coverage_pct,
        "missing_req_ids": missing,
        "is_complete": len(missing) == 0
    }


@mcp.tool(
    name="retrieve_requirement_evidence",
    description="Retrieve all cited evidence chunks, source documents, and page references for a specific requirement."
)
def retrieve_requirement_evidence(
    requirement_id: str,
    compliance_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Returns verified evidence chunks for an individual requirement ID."""
    for item in compliance_matrix:
        if item.get("requirement_id") == requirement_id:
            return {
                "requirement_id": requirement_id,
                "description": item.get("description"),
                "status": item.get("status"),
                "rationale": item.get("rationale"),
                "evidence": item.get("evidence_citations", []),
                "missing_information": item.get("missing_information")
            }
            
    return {"error": f"Requirement {requirement_id} not found in compliance matrix."}


if __name__ == "__main__":
    mcp.run()
