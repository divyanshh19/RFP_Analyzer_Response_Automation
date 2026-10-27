from pydantic import BaseModel
import uuid
from datetime import datetime
from app.models.rfp import RequirementStatus

class ResponseCreate(BaseModel):
    requirement_id: uuid.UUID
    response_text: str

class ResponseUpdate(BaseModel):
    response_text: str

class RequirementStatusUpdate(BaseModel):
    status: RequirementStatus
    
class ResponseDTO(BaseModel):
    id: uuid.UUID
    requirement_id: uuid.UUID
    response_text: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
