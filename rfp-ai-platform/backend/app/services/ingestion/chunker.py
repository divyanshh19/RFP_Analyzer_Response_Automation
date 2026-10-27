import uuid
from typing import List
from app.core.config import settings

class ChunkMetadata:
    def __init__(self, document_id: uuid.UUID, page_number: int, section_name: str, chunk_id: str, text: str):
        self.document_id = document_id
        self.page_number = page_number
        self.section_name = section_name
        self.chunk_id = chunk_id
        self.text = text

def is_likely_heading(text: str) -> bool:
    """Simple heuristic to detect if a line of text is a section heading."""
    if len(text) > 100 or len(text) == 0:
        return False
    # If it's short and title-cased, or doesn't end with standard punctuation
    if text.istitle() or not text.endswith(('.', ':', '?', '!')):
        return True
    return False

def chunk_document(document_id: uuid.UUID, pages: dict[int, str]) -> List[ChunkMetadata]:
    """
    Structure-aware chunker implemented natively. 
    It splits text page-by-page to guarantee page traceability, and respects paragraphs.
    """
    chunks = []
    current_section = "General"
    
    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP

    for page_num, text in pages.items():
        paragraphs = text.split('\n\n')
        current_chunk_text = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Detect section shifts
            if is_likely_heading(para):
                current_section = para
            
            # If adding this paragraph exceeds our size limit, finalize the current chunk
            if len(current_chunk_text) + len(para) > chunk_size and len(current_chunk_text) > 0:
                chunks.append(ChunkMetadata(
                    document_id=document_id,
                    page_number=page_num,
                    section_name=current_section,
                    chunk_id=str(uuid.uuid4()),
                    text=current_chunk_text.strip()
                ))
                
                # Overlap logic: keep the last N characters of the previous chunk to maintain context
                overlap_start = max(0, len(current_chunk_text) - chunk_overlap)
                current_chunk_text = current_chunk_text[overlap_start:] + "\n\n" + para
            else:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
                    
        # Flush the leftover text on this page into a final chunk
        if current_chunk_text.strip():
            chunks.append(ChunkMetadata(
                document_id=document_id,
                page_number=page_num,
                section_name=current_section,
                chunk_id=str(uuid.uuid4()),
                text=current_chunk_text.strip()
            ))
    
    return chunks
