import json
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.retrieval.rag_service import retrieve_relevant_chunks
from app.models.rfp import RequirementStatus

# Dynamic Gemini Client Factory
def get_gemini_client():
    from app.core.config import settings
    return genai.Client(api_key=settings.GEMINI_API_KEY)

# Backwards compatibility reference
client = get_gemini_client()

PROMPT_TEMPLATE = """
You are an expert AI RFP response writer for our enterprise. 
You MUST draft a highly professional response to the following RFP Requirement ONLY using the provided Knowledge Base Context.

REQUIREMENT:
{requirement}

KNOWLEDGE BASE CONTEXT:
{context}

INSTRUCTIONS:
1. If the context contains sufficient evidence, draft a clear, persuasive, and professional response.
2. If the context does NOT contain sufficient evidence to answer the requirement, you MUST output EXACTLY the phrase: "Insufficient evidence in the knowledge base." Do not fabricate or hallucinate any capabilities.
3. Do not mention that you are an AI or reference the context explicitly (e.g., avoid "Based on the provided context"). Just answer directly on behalf of the company.
"""

def generate_draft_response(requirement_text: str) -> dict:
    """
    RAG Pipeline for Response Generation and Gap Analysis via Gemini.
    """
    # 1. Semantic Retrieval (Phase 9)
    chunks = retrieve_relevant_chunks(query=requirement_text, top_k=4)
    
    if not chunks:
        return {
            "response_text": "Insufficient evidence in the knowledge base.",
            "status": RequirementStatus.NEEDS_INFORMATION,
            "sources": []
        }
        
    # 2. Construct Prompt Context
    context_text = "\n\n".join([f"Source: {c.document_type} (Page {c.page_number})\nText: {c.text}" for c in chunks])
    prompt = PROMPT_TEMPLATE.replace("{requirement}", requirement_text).replace("{context}", context_text)
    
    # 3. Generate Grounded Content (Phase 11 via Gemini)
    try:
        gemini_client = get_gemini_client()
        response = gemini_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024
            )
        )
        final_text = response.text.strip()
    except Exception as e:
        print(f"Gemini Generation Error: {e}")
        final_text = "Insufficient evidence in the knowledge base."
    
    # 4. Gap Analysis & Hallucination Prevention (Phase 12)
    status = RequirementStatus.SUPPORTED
    if "Insufficient evidence" in final_text:
        status = RequirementStatus.NEEDS_INFORMATION
        
    return {
        "response_text": final_text,
        "status": status,
        "sources": [c.chunk_id for c in chunks]
    }
