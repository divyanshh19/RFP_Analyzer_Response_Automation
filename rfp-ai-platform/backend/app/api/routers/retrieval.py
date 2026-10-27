from fastapi import APIRouter, Depends
from app.api.deps import CurrentUser
from app.schemas.retrieval import SearchRequest, SearchResult
from app.services.retrieval import rag_service

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

@router.post("/search", response_model=list[SearchResult])
def search_knowledge_base(request: SearchRequest, current_user: CurrentUser):
    """
    Perform semantic vector search against ChromaDB.
    By default, restricts results to KNOWLEDGE_BASE documents to prevent 
    retrieving context from other raw RFP files.
    """
    return rag_service.retrieve_relevant_chunks(
        query=request.query,
        top_k=request.top_k,
        doc_type_filter=request.document_type_filter
    )
