import uuid
from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import SessionDep, CurrentUser
from app.schemas.requirement import RequirementResponse
from app.repositories import document_repo, chunk_repo, requirement_repo
from app.services.extraction import requirement_extractor

router = APIRouter(prefix="/rfp", tags=["rfp"])

@router.post("/{document_id}/extract-requirements", response_model=list[RequirementResponse])
def extract_rfp_requirements(document_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """
    Analyze an ingested RFP document, extract its requirements using Gemini, 
    and persist them to the database.
    """
    doc = document_repo.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not doc.rfp_project_id:
        raise HTTPException(status_code=400, detail="Document is not associated with an RFP Project")
        
    chunks = chunk_repo.get_chunks_for_document(db, document_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document has no chunks. Run the /process pipeline first.")
        
    # Reconstruct text with structural hints. 
    # For documents > 1M tokens, this would require chunked LLM calls, but Gemini handles 1M easily.
    full_text = "\n\n".join([f"Page {c.page_number} [{c.section_name}]: {c.chunk_text}" for c in chunks])
    
    try:
        extracted_reqs = requirement_extractor.extract_requirements_from_text(full_text)
        db_reqs = requirement_repo.create_requirements(
            db=db, 
            project_id=doc.rfp_project_id, 
            document_id=doc.id, 
            reqs_in=extracted_reqs
        )
        return db_reqs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/{project_id}/requirements", response_model=list[RequirementResponse])
def get_rfp_requirements(project_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """Fetch all extracted requirements belonging to an RFP project."""
    return requirement_repo.get_requirements_by_project(db, project_id)
