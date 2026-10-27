from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional
from app.models.document import DocumentType

class DocumentBase(BaseModel):
    name: str
    file_type: str
    document_type: DocumentType
    rfp_project_id: Optional[uuid.UUID] = None

class DocumentCreate(DocumentBase):
    file_path: str

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    processing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
