import uuid
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.api.deps import SessionDep, CurrentUser
from app.models.rfp import RFPProject, Requirement
from app.models.response import Response
import docx

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/{project_id}/docx")
def export_rfp_docx(project_id: uuid.UUID, db: SessionDep, current_user: CurrentUser):
    """Compiles all approved requirements and responses into a formatted DOCX (Phase 13)."""
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
        
    requirements = db.query(Requirement).filter(Requirement.rfp_project_id == project_id).order_by(Requirement.requirement_id).all()
    
    doc = docx.Document()
    doc.add_heading(f"RFP Response: {project.name}", 0)
    
    for req in requirements:
        doc.add_heading(f"[{req.requirement_id}] {req.category} - Priority: {req.priority.value}", level=2)
        doc.add_paragraph(req.description, style='Intense Quote')
        
        resp = db.query(Response).filter(Response.requirement_id == req.id).first()
        if resp:
            doc.add_paragraph(resp.response_text)
        else:
            doc.add_paragraph("No response generated yet.", style='Emphasis')
            
        doc.add_paragraph("-" * 40)
        
    export_dir = os.path.join("data", "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    export_path = os.path.join(export_dir, f"{project_id}.docx")
    doc.save(export_path)
    
    return FileResponse(
        path=export_path, 
        filename=f"{project.name}_Final_Response.docx", 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
