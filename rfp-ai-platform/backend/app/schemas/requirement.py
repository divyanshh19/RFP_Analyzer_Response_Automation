from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from app.models.rfp import RequirementStatus, RequirementPriority

class RequirementCreate(BaseModel):
    requirement_id: str
    description: str
    category: str
    priority: RequirementPriority
    mandatory: bool
    deadline: Optional[datetime] = None
    deliverable: Optional[str] = None
    compliance: Optional[List[str]] = []
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class RequirementResponse(BaseModel):
    id: uuid.UUID
    rfp_project_id: uuid.UUID
    requirement_id: str
    description: str
    category: str
    priority: RequirementPriority
    mandatory: bool
    status: RequirementStatus
    source_document_id: Optional[uuid.UUID]
    
    model_config = {"from_attributes": True}
