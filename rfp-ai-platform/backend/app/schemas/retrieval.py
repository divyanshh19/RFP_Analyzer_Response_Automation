from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    chunk_id: str
    text: str
    document_id: str
    document_type: str
    page_number: int
    section_name: str
    similarity_score: float

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    document_type_filter: Optional[str] = "KNOWLEDGE_BASE"
