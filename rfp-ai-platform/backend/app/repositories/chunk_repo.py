from sqlalchemy.orm import Session
from typing import List
from app.models.document import DocumentChunk
from app.services.ingestion.chunker import ChunkMetadata
import uuid

def save_chunks(db: Session, chunks_data: List[ChunkMetadata]) -> List[DocumentChunk]:
    db_chunks = []
    for c in chunks_data:
        db_chunk = DocumentChunk(
            document_id=c.document_id,
            chunk_id=c.chunk_id,
            page_number=c.page_number,
            section_name=c.section_name,
            chunk_text=c.text
        )
        db_chunks.append(db_chunk)
    
    # Bulk save for high performance on massive RFPs
    db.bulk_save_objects(db_chunks)
    db.commit()
    return db_chunks

def get_chunks_for_document(db: Session, document_id: uuid.UUID) -> List[DocumentChunk]:
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
