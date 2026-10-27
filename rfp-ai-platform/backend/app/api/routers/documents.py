import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.schemas.document import DocumentResponse
from app.models.document import DocumentType
from app.services import document_service
from app.services.extraction import text_extractor
from app.services.ingestion import pipeline
from app.repositories import document_repo

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    db: SessionDep,
    current_user: CurrentUser, # Requires Auth token
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    rfp_project_id: uuid.UUID = Form(None)
):
    """
    Upload a new RFP document or Knowledge Base file.
    Only supports PDF and DOCX formats.
    """
    return await document_service.process_upload(
        db=db, 
        file=file, 
        document_type=document_type, 
        rfp_project_id=rfp_project_id
    )

@router.get("/", response_model=list[DocumentResponse])
def list_documents(db: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    """List all documents uploaded in the system."""
    return document_repo.get_documents(db, skip=skip, limit=limit)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """Retrieve metadata for a specific document."""
    doc = document_repo.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{document_id}/extract")
def extract_document_text_api(document_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """
    Trigger manual text extraction on an uploaded document (Test Endpoint).
    Returns text preview and flags if OCR is required.
    """
    doc = document_repo.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        result = text_extractor.extract_document_text(doc.file_path, doc.file_type)
        return {
            "document_id": doc.id,
            "needs_ocr": result.needs_ocr,
            "total_pages": len(result.pages),
            "text_preview": result.text[:500] + "..." if len(result.text) > 500 else result.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/process")
def process_document_api(document_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """
    Executes the ingestion pipeline (Phase 5/6 Extraction + Phase 7 Chunking).
    Updates document status and creates DocumentChunk records in MySQL.
    """
    try:
        result = pipeline.process_document_pipeline(db, document_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
