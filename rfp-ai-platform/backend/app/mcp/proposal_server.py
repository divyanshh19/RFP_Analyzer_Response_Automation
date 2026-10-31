"""
Proposal MCP Server
Exposes standardized Model Context Protocol (MCP) tools for drafting grounded proposal sections,
validating factual assertions, revising drafts, and exporting formatted Word DOCX response packages.
"""

import json
import os
import sys
import uuid
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from google import genai
from google.genai import types

mcp = FastMCP("proposal-server")

def _get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)


@mcp.tool(
    name="generate_proposal_section",
    description="Generate a professional, persuasive proposal section (Executive Summary, Technical Architecture, Compliance Response, Security & SLAs) grounded exclusively in retrieved company evidence."
)
def generate_proposal_section(
    section_name: str,
    requirements: List[Dict[str, Any]],
    evidence_chunks: List[Dict[str, Any]],
    tone: str = "Formal and Persuasive"
) -> Dict[str, Any]:
    """Generates an evidence-grounded proposal section."""
    client = _get_gemini_client()
    
    req_context = "\n".join([f"- [{r.get('requirement_id')}] ({r.get('category')}): {r.get('description')}" for r in requirements[:15]])
    evidence_context = "\n\n".join([f"[Source: {c.get('document_type', 'KB')}, Page {c.get('page_number', '1')}]\n{c.get('text', '')}" for c in evidence_chunks[:10]])
    
    prompt = f"""
You are an elite Senior Bid & Proposal Manager.
Write the '{section_name}' section for our formal tender proposal response.

REQUIREMENTS TO ADDRESS:
{req_context}

VERIFIED COMPANY EVIDENCE:
{evidence_context}

INSTRUCTIONS:
1. Tone: {tone}.
2. Speak directly on behalf of the company ("We", "Our solution", "Our team").
3. You MUST ground every factual capability, metric, architecture detail, and timeline strictly in the provided COMPANY EVIDENCE.
4. If certain requirements lack supporting evidence, explicitly state what clarification is required or that custom deployment will be specified upon contract kickoff—DO NOT hallucinate certifications or capabilities.
5. Structure the section with clear markdown headings, concise paragraphs, and bullet points.

Return a valid JSON object:
{{
  "section_name": "{section_name}",
  "content": "Full markdown proposal text",
  "addressed_requirement_ids": ["REQ-001"],
  "factual_assertions_count": 5
}}
"""
    try:
        resp = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=3000
            )
        )
        return json.loads(resp.text)
    except Exception as e:
        return {
            "section_name": section_name,
            "content": f"Failed to generate section due to: {str(e)}",
            "addressed_requirement_ids": [],
            "error": str(e)
        }


@mcp.tool(
    name="validate_proposal_content",
    description="Critique and validate proposal section drafts against evidence chunks to detect unsupported claims, hallucinated metrics, or missing requirement coverage."
)
def validate_proposal_content(
    section_text: str,
    evidence_chunks: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Performs automated quality assurance and evidence traceability verification."""
    client = _get_gemini_client()
    
    evidence_context = "\n\n".join([f"[{c.get('chunk_id')}] {c.get('text')}" for c in evidence_chunks[:10]])
    req_list = ", ".join([r.get("requirement_id", "") for r in requirements[:15]])
    
    prompt = f"""
You are an expert Proposal Compliance QA Reviewer. 
Review this proposal text against our verified company evidence and mandatory requirement list.

PROPOSAL SECTION TEXT:
{section_text}

VERIFIED COMPANY EVIDENCE:
{evidence_context}

MANDATORY REQUIREMENT IDS:
{req_list}

AUDIT OBJECTIVES:
1. Identify any unsupported claims, exaggerated numbers, or hallucinated certifications.
2. Verify if the content adequately addresses the listed requirements.
3. Recommend specific wording improvements or corrections.

Return a valid JSON object:
{{
  "is_valid": true or false,
  "confidence_score": 0.0 to 1.0,
  "unsupported_claims": ["List of any unverified claims found, or empty list"],
  "covered_requirements": ["REQ-001"],
  "critique": "Overall critique and specific instructions for revision if invalid, or 'Approved' if valid"
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
        return json.loads(resp.text)
    except Exception as e:
        return {
            "is_valid": False,
            "confidence_score": 0.0,
            "unsupported_claims": [],
            "covered_requirements": [],
            "critique": f"Validation execution error: {str(e)}"
        }


@mcp.tool(
    name="revise_proposal_section",
    description="Revise a proposal section by incorporating reviewer critique, correcting unverified assertions, or expanding evidence."
)
def revise_proposal_section(
    section_text: str,
    critique: str,
    additional_evidence: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Applies reviewer feedback to rewrite and polish a draft section."""
    client = _get_gemini_client()
    
    extra_evidence_text = ""
    if additional_evidence:
        extra_evidence_text = "ADDITIONAL EVIDENCE:\n" + "\n\n".join([f"[{c.get('chunk_id')}] {c.get('text')}" for c in additional_evidence[:5]])
        
    prompt = f"""
You are an expert Bid Writer revising a proposal draft based on strict review feedback.

ORIGINAL DRAFT:
{section_text}

REVIEWER CRITIQUE & REQUIRED CHANGES:
{critique}

{extra_evidence_text}

INSTRUCTIONS:
1. Correct any unsupported claims highlighted in the critique.
2. Preserve strong, grounded technical explanations.
3. Polish readability and flow.

Return a valid JSON object:
{{
  "revised_content": "Full revised proposal text in clean markdown",
  "changes_made": ["Summary of key changes"]
}}
"""
    try:
        resp = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return json.loads(resp.text)
    except Exception as e:
        return {
            "revised_content": section_text,
            "changes_made": [],
            "error": str(e)
        }


@mcp.tool(
    name="save_proposal_draft",
    description="Persist proposal draft sections into the local data repository."
)
def save_proposal_draft(
    project_id: str,
    section_name: str,
    content: str
) -> Dict[str, Any]:
    """Saves a section draft to disk/storage."""
    try:
        draft_dir = os.path.join(backend_dir, "data", "proposals", str(project_id))
        os.makedirs(draft_dir, exist_ok=True)
        
        safe_name = "".join([c if c.isalnum() or c in "._-" else "_" for c in section_name])
        file_path = os.path.join(draft_dir, f"{safe_name}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {
            "success": True,
            "project_id": project_id,
            "section_name": section_name,
            "file_path": file_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool(
    name="export_proposal",
    description="Compile all finalized proposal sections, compliance matrices, and source citations into a professional Word DOCX document ready for submission."
)
def export_proposal(
    project_id: str,
    title: str,
    sections: List[Dict[str, Any]],
    compliance_matrix: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Builds a formatted Microsoft Word (.docx) proposal package."""
    try:
        doc = docx.Document()
        
        # Document Title
        title_p = doc.add_heading(title, 0)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Subtitle
        sub_p = doc.add_paragraph("Enterprise Tender Response & Compliance Matrix")
        sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_p.runs[0].font.size = Pt(13)
        sub_p.runs[0].font.color.rgb = RGBColor(100, 100, 100)
        
        doc.add_paragraph("-" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 1. Executive Proposal Sections
        for sec in sections:
            name = sec.get("section_name", "Proposal Section")
            content = sec.get("content", "")
            
            doc.add_heading(name, level=1)
            for paragraph_text in content.split("\n\n"):
                clean = paragraph_text.strip()
                if clean.startswith("#"):
                    continue # skip markdown title duplicates
                if clean:
                    doc.add_paragraph(clean)
            doc.add_paragraph("")
            
        # 2. Compliance Matrix Table
        if compliance_matrix:
            doc.add_page_break()
            doc.add_heading("Requirements Compliance & Traceability Matrix", level=1)
            
            table = doc.add_table(rows=1, cols=4)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True
            
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Req ID"
            hdr_cells[1].text = "Requirement Description"
            hdr_cells[2].text = "Compliance Status"
            hdr_cells[3].text = "Evidence & Rationale"
            
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True
                            run.font.size = Pt(10)
                            
            for item in compliance_matrix:
                row_cells = table.add_row().cells
                row_cells[0].text = item.get("requirement_id", "REQ")
                row_cells[1].text = item.get("description", "")
                row_cells[2].text = item.get("status", "Non-compliant")
                row_cells[3].text = item.get("rationale", "")
                
                for cell in row_cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(9)
                            
        # Save file
        export_dir = os.path.join(backend_dir, "data", "exports")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, f"{project_id}_Final_Proposal.docx")
        doc.save(file_path)
        
        return {
            "success": True,
            "project_id": project_id,
            "file_path": file_path,
            "file_name": f"{title.replace(' ', '_')}_Response.docx"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
