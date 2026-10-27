import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.document import DocumentType
from app.schemas.document import DocumentCreate
from app.repositories import document_repo

# Ensure the upload directory exists relative to the backend folder
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "data", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    # Sometimes browsers send docx as generic octet-stream depending on OS, but we stick to strict checking for now.
}

async def process_upload(
    db: Session, 
    file: UploadFile, 
    document_type: DocumentType, 
    rfp_project_id: uuid.UUID | None = None
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}. Only PDF and DOCX are allowed."
        )
    
    file_ext = ALLOWED_MIME_TYPES[file.content_type]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.normpath(os.path.join(UPLOAD_DIR, unique_filename))

    # Save physical file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        await file.close()
    
    # Create DB record
    doc_create = DocumentCreate(
        name=file.filename,
        file_type=file_ext,
        document_type=document_type,
        file_path=file_path,
        rfp_project_id=rfp_project_id
    )
    
    return document_repo.create_document(db, doc_create)
