import uuid
from sqlalchemy.orm import Session
from app.models.response import Response
from app.schemas.response import ResponseCreate

def upsert_response(db: Session, resp_in: ResponseCreate) -> Response:
    existing = db.query(Response).filter(Response.requirement_id == resp_in.requirement_id).first()
    if existing:
        existing.ai_response = resp_in.response_text
        db.commit()
        db.refresh(existing)
        return existing
        
    new_resp = Response(
        requirement_id=resp_in.requirement_id,
        ai_response=resp_in.response_text
    )
    db.add(new_resp)
    db.commit()
    db.refresh(new_resp)
    return new_resp
