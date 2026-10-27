import uuid
from fastapi import APIRouter, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.models.rfp import Requirement
from app.schemas.response import ResponseDTO, RequirementStatusUpdate, ResponseUpdate, ResponseCreate
from app.services.generation import response_generator
from app.repositories import response_repo

router = APIRouter(prefix="/generation", tags=["generation"])

@router.post("/{requirement_id}/draft", response_model=dict)
def generate_response(requirement_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """Generates an AI response for a requirement via RAG (Phase 11 & 12)."""
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    result = response_generator.generate_draft_response(req.description)
    
    # Update status for gap analysis
    req.status = result["status"]
    db.commit()
    
    # Upsert the draft
    resp_in = ResponseCreate(
        requirement_id=req.id,
        response_text=result["response_text"]
    )
    saved_resp = response_repo.upsert_response(db, resp_in)
    
    return {
        "id": saved_resp.id,
        "response_text": saved_resp.ai_response,
        "status": req.status,
        "sources": result["sources"]
    }
    
@router.put("/responses/{response_id}")
def manual_edit_response(response_id: uuid.UUID, update_data: ResponseUpdate, db: SessionDep, current_user: CurrentUser):
    """Allows a human reviewer to manually override the AI response (Phase 14)."""
    from app.models.response import Response
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404)
        
    resp.final_response = update_data.response_text
    db.commit()
    db.refresh(resp)
    return {"status": "success", "response_text": resp.final_response or resp.ai_response}
    
@router.put("/requirements/{requirement_id}/status")
def approve_reject_requirement(requirement_id: uuid.UUID, update_data: RequirementStatusUpdate, db: SessionDep, current_user: CurrentUser):
    """Approve or reject a requirement status manually (Phase 14)."""
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404)
        
    req.status = update_data.status
    db.commit()
    return {"status": "success", "new_status": req.status}
