import uuid
from sqlalchemy.orm import Session
from app.repositories import document_repo, chunk_repo
from app.services.extraction import text_extractor
from app.services.ingestion import chunker

from app.services.vector_store.chroma_client import chroma_manager
from app.services.embeddings import embedding_service

def process_document_pipeline(db: Session, document_id: uuid.UUID):
    """
    Orchestrates the ingestion lifecycle: Extraction -> Chunking -> Database -> Vector Embedding.
    """
    doc = document_repo.get_document(db, document_id)
    if not doc:
        raise ValueError("Document not found")
        
    # Phase 5 & 6: Extract Text (with automated OCR fallback)
    doc.processing_status = "EXTRACTING"
    db.commit()
    
    try:
        extraction_result = text_extractor.extract_document_text(doc.file_path, doc.file_type)
    except Exception as e:
        doc.processing_status = "FAILED_EXTRACTION"
        db.commit()
        raise e
        
    # Phase 7: Chunking & Metadata Structuring
    doc.processing_status = "CHUNKING"
    db.commit()
    
    try:
        chunks = chunker.chunk_document(doc.id, extraction_result.pages)
        chunk_repo.save_chunks(db, chunks)
    except Exception as e:
        doc.processing_status = "FAILED_CHUNKING"
        db.commit()
        raise e
        
    # Phase 8: Embeddings & Vector Storage
    doc.processing_status = "EMBEDDING"
    db.commit()
    
    try:
        collection = chroma_manager.get_collection()
        
        ids = []
        texts = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk.chunk_id)
            texts.append(chunk.text)
            metadatas.append({
                "document_id": str(chunk.document_id),
                "document_type": doc.document_type.value,
                "page_number": chunk.page_number,
                "section_name": chunk.section_name
            })
            
        if texts:
            embeddings = embedding_service.get_embeddings_batch(texts)
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
    except Exception as e:
        doc.processing_status = "FAILED_EMBEDDING"
        db.commit()
        raise e
        
    doc.processing_status = "COMPLETED"
    db.commit()
    
    return {
        "status": "success", 
        "document_id": doc.id, 
        "chunks_created": len(chunks),
        "needs_ocr_flag": extraction_result.needs_ocr
    }
