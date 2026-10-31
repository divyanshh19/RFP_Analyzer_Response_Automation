"""
Knowledge Base MCP Server
Exposes standardized Model Context Protocol (MCP) tools for searching enterprise
knowledge bases, past proposals, certifications, company capabilities, and case studies.
"""

import os
import sys
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.retrieval import rag_service

mcp = FastMCP("knowledge-base-server")


def _format_chunk(res) -> Dict[str, Any]:
    return {
        "chunk_id": res.chunk_id,
        "text": res.text,
        "document_id": res.document_id,
        "document_type": res.document_type,
        "page_number": res.page_number,
        "section_name": res.section_name or "N/A",
        "similarity_score": round(res.similarity_score, 4)
    }


@mcp.tool(
    name="search_company_documents",
    description="Perform semantic vector search across all verified company documents in the enterprise knowledge base."
)
def search_company_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieves top-k relevant chunks from company profile and capability documents."""
    try:
        results = rag_service.retrieve_relevant_chunks(query=query, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


@mcp.tool(
    name="search_previous_proposals",
    description="Search previously submitted winning proposals and bid archives for precedent response phrasing."
)
def search_previous_proposals(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Queries for previous proposal text matching the query."""
    try:
        augmented_query = f"previous proposal bid submission response: {query}"
        results = rag_service.retrieve_relevant_chunks(query=augmented_query, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


@mcp.tool(
    name="retrieve_company_capabilities",
    description="Retrieve verified company technical capabilities, infrastructure specs, architecture capabilities, and SLAs for a given domain."
)
def retrieve_company_capabilities(domain: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Fetches capability statements for a specific technical domain (e.g., 'Cloud Security', '24/7 Support')."""
    try:
        augmented_query = f"company capability technical architecture specification: {domain}"
        results = rag_service.retrieve_relevant_chunks(query=augmented_query, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


@mcp.tool(
    name="retrieve_certifications",
    description="Search for evidence of enterprise security, quality, and industry certifications (e.g. ISO 27001, SOC 2, HIPAA, CMMI)."
)
def retrieve_certifications(certification_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Searches knowledge base for certifications, audit reports, and compliance attestations."""
    try:
        augmented_query = f"certified accreditation audit compliance standard: {certification_name}"
        results = rag_service.retrieve_relevant_chunks(query=augmented_query, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


@mcp.tool(
    name="retrieve_relevant_experience",
    description="Retrieve past project performance, client case studies, and reference implementations for an industry or scope."
)
def retrieve_relevant_experience(industry: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Finds relevant past performance, client case studies, and success stories."""
    try:
        augmented_query = f"past performance case study project track record client reference in: {industry}"
        results = rag_service.retrieve_relevant_chunks(query=augmented_query, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


@mcp.tool(
    name="search_supporting_evidence",
    description="Deep search for evidence directly matching a specific RFP requirement text with citation metadata."
)
def search_supporting_evidence(requirement_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieves evidence chunks formatted for compliance analysis and traceability."""
    try:
        results = rag_service.retrieve_relevant_chunks(query=requirement_text, top_k=top_k, doc_type_filter="KNOWLEDGE_BASE")
        return [_format_chunk(r) for r in results]
    except Exception as e:
        return [{"error": str(e), "chunk_id": "ERR", "text": ""}]


if __name__ == "__main__":
    mcp.run()
