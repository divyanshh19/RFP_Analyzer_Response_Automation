import uuid
from sqlalchemy.orm import Session
from typing import List
from app.models.rfp import Requirement, RequirementStatus
from app.schemas.requirement import RequirementCreate

def create_requirements(
    db: Session, 
    project_id: uuid.UUID, 
    document_id: uuid.UUID, 
    reqs_in: List[RequirementCreate]
) -> List[Requirement]:
    db_reqs = []
    for r in reqs_in:
        db_req = Requirement(
            rfp_project_id=project_id,
            requirement_id=r.requirement_id,
            description=r.description,
            category=r.category,
            priority=r.priority,
            mandatory=r.mandatory,
            deadline=r.deadline,
            deliverable=r.deliverable,
            compliance=",".join(r.compliance) if r.compliance else None,
            status=RequirementStatus.PENDING,
            source_document_id=document_id,
            source_page=r.source_page,
            source_section=r.source_section
        )
        db_reqs.append(db_req)
        
    db.bulk_save_objects(db_reqs)
    db.commit()
    return db_reqs
    
def get_requirements_by_project(db: Session, project_id: uuid.UUID) -> List[Requirement]:
    return db.query(Requirement).filter(Requirement.rfp_project_id == project_id).all()
