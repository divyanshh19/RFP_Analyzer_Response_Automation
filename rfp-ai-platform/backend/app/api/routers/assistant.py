"""
FastAPI Router for AI Assistant / RFP Copilot.
Exposes interactive conversational endpoints with multi-turn history and context retrieval.
"""

import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import SessionDep, CurrentUser
from app.services.assistant.copilot_service import copilot_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatMessageRequest(BaseModel):
    project_id: uuid.UUID
    message: str


@router.post("/chat")
def chat_with_copilot(
    data: ChatMessageRequest,
    current_user: CurrentUser
):
    """Sends a question to the AI Copilot with project-specific context."""
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    result = copilot_service.chat(
        user_id=str(current_user.id),
        project_id=str(data.project_id),
        message=data.message
    )
    return result


@router.get("/{project_id}/history")
def get_chat_history(
    project_id: uuid.UUID,
    current_user: CurrentUser
):
    """Retrieves multi-turn conversation history for this user and project."""
    history = copilot_service.get_history(
        user_id=str(current_user.id),
        project_id=str(project_id)
    )
    return {"history": history}


@router.delete("/{project_id}/history")
def clear_chat_history(
    project_id: uuid.UUID,
    current_user: CurrentUser
):
    """Clears conversation history for this user and project."""
    copilot_service.clear_history(
        user_id=str(current_user.id),
        project_id=str(project_id)
    )
    return {"status": "success", "message": "Chat history cleared"}
