import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from app.api.deps import SessionDep, CurrentUser
from app.models.rfp import RFPProject

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    
router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("")
def create_project(data: ProjectCreate, db: SessionDep, current_user: CurrentUser):
    project = RFPProject(user_id=current_user.id, name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
    
@router.get("")
def list_projects(db: SessionDep, current_user: CurrentUser):
    return db.query(RFPProject).filter(RFPProject.user_id == current_user.id).all()
    
@router.get("/{project_id}")
def get_project(project_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    return db.query(RFPProject).filter(RFPProject.id == project_id, RFPProject.user_id == current_user.id).first()
