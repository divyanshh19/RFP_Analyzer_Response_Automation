"""
RFP Document MCP Server
Exposes standardized Model Context Protocol (MCP) tools for RFP document extraction,
parsing, deadline identification, criteria extraction, and requirements analysis.
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.services.extraction import text_extractor
from app.services.extraction import requirement_extractor
from google import genai
from google.genai import types

mcp = FastMCP("rfp-document-server")

def _get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)


class ExtractionResultSchema(BaseModel):
    total_pages: int
    char_count: int
    needs_ocr: bool
    text: str
    pages: Dict[int, str] = Field(default_factory=dict)


@mcp.tool(
    name="extract_rfp_text",
    description="Extract digital or scanned text from an RFP document (PDF or DOCX) with automated OCR fallback."
)
def extract_rfp_text(file_path: str, file_type: str = "pdf") -> Dict[str, Any]:
    """Extracts raw text and per-page mappings from a PDF or DOCX file."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}", "success": False}
        
    try:
        res = text_extractor.extract_document_text(file_path=file_path, file_type=file_type)
        return {
            "success": True,
            "total_pages": len(res.pages),
            "char_count": len(res.text),
            "needs_ocr": res.needs_ocr,
            "text": res.text,
            "page_keys": list(res.pages.keys())
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@mcp.tool(
    name="extract_rfp_requirements",
    description="Extract line-item technical, functional, security, and operational requirements from document text into structured records."
)
def extract_rfp_requirements(text: str) -> List[Dict[str, Any]]:
    """Analyzes RFP text using Gemini 3.5 Flash to extract line-item requirements."""
    if not text or len(text.strip()) == 0:
        return []
        
    # Strictly raise exceptions so the agent node accurately detects failures / quota blocks.
    # NEVER convert infrastructure errors into fake or synthetic requirements (e.g. ERR-001).
    reqs = requirement_extractor.extract_requirements_from_text(text)
    return [r.model_dump() for r in reqs]


@mcp.tool(
    name="extract_deadlines",
    description="Extract submission deadlines, question/clarification cutoff dates, award notices, and contract milestones from RFP text."
)
def extract_deadlines(text: str) -> List[Dict[str, Any]]:
    """Identifies all critical dates and deadlines mentioned in the RFP text."""
    if not text:
        return []
        
    prompt = f"""
You are an expert procurement analyst. Extract all dates, timelines, and deadlines from this RFP text.
Return a valid JSON array of objects with schema:
[
  {{
    "event": "e.g., Submission Deadline, Pre-bid Meeting, Q&A Cutoff, Award Date, Project Kickoff",
    "date": "YYYY-MM-DD or string description if exact date is unspecified",
    "time": "e.g., 5:00 PM EST or null",
    "mandatory": true,
    "source_context": "short quote from document"
  }}
]

DOCUMENT TEXT (excerpt):
{text[:20000]}
"""
    try:
        client = _get_gemini_client()
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
        raise RuntimeError(f"Deadline extraction failed: {str(e)}") from e


@mcp.tool(
    name="extract_eligibility_criteria",
    description="Extract mandatory bidder qualification and eligibility criteria (years in business, revenue, clearances, legal standing)."
)
def extract_eligibility_criteria(text: str) -> List[Dict[str, Any]]:
    """Extracts bidder eligibility and minimum qualification conditions."""
    if not text:
        return []
        
    prompt = f"""
Extract all mandatory bidder eligibility criteria, minimum qualifications, and certifications required to bid on this tender.
Return a valid JSON array of objects:
[
  {{
    "criterion_id": "ELIG-001",
    "description": "Full criterion text",
    "category": "Financial, Experience, Certification, Legal, or Personnel",
    "mandatory": true,
    "proof_required": "e.g. Audited balance sheets, Certificate of Incorporation"
  }}
]

DOCUMENT TEXT:
{text[:20000]}
"""
    try:
        client = _get_gemini_client()
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
        raise RuntimeError(f"Eligibility criteria extraction failed: {str(e)}") from e


@mcp.tool(
    name="extract_evaluation_criteria",
    description="Extract technical and financial scoring rubrics, weighting percentages, and evaluation methodology."
)
def extract_evaluation_criteria(text: str) -> List[Dict[str, Any]]:
    """Extracts technical/financial evaluation weights and scoring matrix."""
    if not text:
        return []
        
    prompt = f"""
Extract the evaluation and scoring criteria from this RFP document.
Return a valid JSON array:
[
  {{
    "criterion": "e.g., Technical Capability, Relevant Experience, Key Personnel, Cost / Pricing",
    "weight_percentage": float or null (e.g. 30.0 for 30%),
    "description": "Details of what is evaluated",
    "scoring_scale": "e.g., 0-100 or 1-5"
  }}
]

DOCUMENT TEXT:
{text[:20000]}
"""
    try:
        client = _get_gemini_client()
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
        raise RuntimeError(f"Evaluation criteria extraction failed: {str(e)}") from e


@mcp.tool(
    name="extract_mandatory_documents",
    description="Extract the list of required forms, attachments, and declarations that must be submitted with the bid."
)
def extract_mandatory_documents(text: str) -> List[Dict[str, Any]]:
    """Extracts required submission documents and forms."""
    if not text:
        return []
        
    prompt = f"""
Identify all mandatory attachments, annexures, forms, certifications, and documentation that must be included in the bid submission.
Return a valid JSON array:
[
  {{
    "document_name": "e.g., Technical Proposal, Annexure B Financial Bid, ISO 27001 Certificate, Non-Disclosure Agreement",
    "format": "e.g., PDF, Excel, Signed Hardcopy",
    "required": true,
    "description": "What the document covers"
  }}
]

DOCUMENT TEXT:
{text[:20000]}
"""
    try:
        client = _get_gemini_client()
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
        raise RuntimeError(f"Mandatory documents extraction failed: {str(e)}") from e


if __name__ == "__main__":
    # Standard MCP stdio transport
    mcp.run()
