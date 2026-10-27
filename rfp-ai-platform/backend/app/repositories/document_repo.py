import uuid
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate

def create_document(db: Session, doc_in: DocumentCreate) -> Document:
    db_doc = Document(
        name=doc_in.name,
        file_type=doc_in.file_type,
        file_path=doc_in.file_path,
        document_type=doc_in.document_type,
        rfp_project_id=doc_in.rfp_project_id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_document(db: Session, document_id: uuid.UUID) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100) -> list[Document]:
    return db.query(Document).offset(skip).limit(limit).all()
