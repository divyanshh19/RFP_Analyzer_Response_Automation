"""
AI Assistant / RFP Copilot Service.
Provides context-aware multi-turn guidance across RFP understanding,
compliance intelligence, proposal writing assistance, and workflow status.
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.services.agent.workflow_manager import workflow_manager
from app.mcp.client import mcp_client
from google import genai
from google.genai import types

# In-memory session history store: key = f"{user_id}:{project_id}"
_conversation_store: Dict[str, List[Dict[str, Any]]] = {}

def _get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key)


COPILOT_SYSTEM_PROMPT = """
You are the enterprise RFP Copilot and Proposal Intelligence Specialist.
You have real-time access to the current project context, workflow execution state,
extracted tender requirements, company knowledge-base evidence, compliance matrix, and proposal drafts.

CORE RESPONSIBILITIES:
1. RFP Question Answering: Explain tender clauses, mandatory criteria, deadlines, and deliverables with exact citations.
2. Compliance Intelligence: Explain why requirements are marked Compliant, Partially Compliant, or Non-Compliant; explain missing evidence.
3. Proposal Writing Copilot: Assist with refining executive summaries, drafting technical narratives, and improving persuasive tone.
4. Workflow Intelligence: Report the current active agent, completed stages, and next actions based strictly on actual workflow state.

CRITICAL RULES:
- Never fabricate company certifications, case studies, or SLAs.
- If information is not in the provided project context or retrieved evidence, say: "This is not documented in the current knowledge base or RFP."
- Provide clear markdown formatting with bullet points and bold key terms.
- Cite sources as [Page X, Section Y] where available.
"""


class RFPCopilotService:
    @staticmethod
    def get_session_key(user_id: str, project_id: str) -> str:
        return f"{user_id}:{project_id}"
        
    @classmethod
    def get_history(cls, user_id: str, project_id: str) -> List[Dict[str, Any]]:
        key = cls.get_session_key(user_id, project_id)
        return _conversation_store.get(key, [])
        
    @classmethod
    def clear_history(cls, user_id: str, project_id: str):
        key = cls.get_session_key(user_id, project_id)
        if key in _conversation_store:
            _conversation_store[key] = []
            
    @classmethod
    def chat(
        cls,
        user_id: str,
        project_id: str,
        message: str,
        context_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Processes a user question, retrieves relevant context/tools, and generates a grounded response."""
        session_key = cls.get_session_key(user_id, project_id)
        if session_key not in _conversation_store:
            _conversation_store[session_key] = []
            
        history = _conversation_store[session_key]
        
        # 1. Fetch live project workflow state
        state = workflow_manager.get_workflow_state(project_id) or {}
        
        # 2. Build live context summary
        status = state.get("workflow_status", "NOT_STARTED")
        reqs = state.get("requirements", [])
        deadlines = state.get("deadlines", [])
        eligibility = state.get("eligibility_criteria", [])
        metrics = state.get("compliance_score_metrics", {})
        gaps = state.get("identified_gaps", [])
        sections = state.get("draft_sections", [])
        
        project_summary = f"""
PROJECT STATE:
- Workflow Status: {status}
- Total Requirements: {len(reqs)}
- Compliance Score: {metrics.get('overall_score', 'N/A')}%
- Mandatory Requirements Score: {metrics.get('mandatory_compliance_score', 'N/A')}%
- Identified Gaps / Missing Items: {len(gaps)}
- Deadlines Found: {len(deadlines)}
- Sections Drafted: {[s.get('section_name') for s in sections]}
"""

        # 3. Dynamic Tool Calling / Evidence Retrieval
        tools_used = []
        retrieved_chunks = []
        
        msg_lower = message.lower()
        if any(term in msg_lower for term in ["search", "capability", "experience", "certification", "evidence", "support", "iso", "soc"]):
            search_tool = mcp_client.get_tool("search_company_documents")
            if search_tool:
                tools_used.append("search_company_documents")
                chunks = search_tool.invoke({"query": message, "top_k": 3})
                if isinstance(chunks, list):
                    retrieved_chunks.extend(chunks)
                    
        # Evidence context block
        evidence_context = ""
        if retrieved_chunks:
            evidence_context = "RETRIEVED KNOWLEDGE BASE EVIDENCE:\n" + "\n\n".join([
                f"[Source: {c.get('document_type', 'KB')}, Page {c.get('page_number', '1')}]\n{c.get('text', '')}"
                for c in retrieved_chunks if c.get("text")
            ])
            
        # Recent multi-turn conversation
        recent_history = history[-6:]
        history_text = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in recent_history])
        
        prompt = f"""
{COPILOT_SYSTEM_PROMPT}

CURRENT PROJECT CONTEXT:
{project_summary}

{evidence_context}

CONVERSATION HISTORY:
{history_text}

USER QUERY:
{message}

INSTRUCTIONS:
Respond comprehensively and professionally.
Suggest 2-3 relevant follow-up questions the user might ask next.
Return a valid JSON object:
{{
  "answer": "Detailed markdown response",
  "citations": [
    {{"source": "Company Profile / RFP", "page": 1, "quote": "Short excerpt"}}
  ],
  "suggested_followups": [
    "What are our non-compliant requirements?",
    "Can you improve the Executive Summary draft?"
  ]
}}
"""
        client = _get_gemini_client()
        try:
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            data = json.loads(resp.text)
            answer_text = data.get("answer", "I could not formulate an answer.")
            citations = data.get("citations", [])
            followups = data.get("suggested_followups", [])
        except Exception as e:
            answer_text = f"I encountered an error querying the intelligence engine: {str(e)}"
            citations = []
            followups = ["What is the current workflow status?", "Show extracted requirements."]
            
        # Save to history
        timestamp = datetime.now(timezone.utc).isoformat()
        history.append({"role": "user", "content": message, "timestamp": timestamp})
        history.append({
            "role": "assistant",
            "content": answer_text,
            "citations": citations,
            "tools_used": tools_used,
            "suggested_followups": followups,
            "timestamp": timestamp
        })
        
        return {
            "answer": answer_text,
            "citations": citations,
            "tools_used": tools_used,
            "suggested_followups": followups,
            "timestamp": timestamp
        }


copilot_service = RFPCopilotService()
