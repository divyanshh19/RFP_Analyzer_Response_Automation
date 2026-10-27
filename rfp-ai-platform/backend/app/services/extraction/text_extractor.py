import fitz  # PyMuPDF
import docx
import os

class TextExtractionResult:
    def __init__(self, text: str, pages: dict[int, str], needs_ocr: bool = False):
        self.text = text
        self.pages = pages
        self.needs_ocr = needs_ocr

def extract_text_from_pdf(file_path: str) -> TextExtractionResult:
    doc = fitz.open(file_path)
    full_text = []
    pages_dict = {}
    total_chars = 0
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        clean_text = text.strip()
        
        pages_dict[page_num + 1] = clean_text  # 1-indexed page mapping for citations
        full_text.append(clean_text)
        total_chars += len(clean_text)
        
    combined_text = "\n\n".join(full_text)
    
    # Simple heuristic: If average digital characters per page is extremely low, it's likely a scanned PDF.
    needs_ocr = False
    if len(doc) > 0 and (total_chars / len(doc)) < 50:
        needs_ocr = True
        
    return TextExtractionResult(text=combined_text, pages=pages_dict, needs_ocr=needs_ocr)

def extract_text_from_docx(file_path: str) -> TextExtractionResult:
    doc = docx.Document(file_path)
    full_text = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
            
    combined_text = "\n\n".join(full_text)
    
    # Note: DOCX formats are flow-based; reliable page number extraction isn't natively supported 
    # without MS Word interop. We treat it as one contiguous chunk (Page 1) for citation basics.
    pages_dict = {1: combined_text}
    
    return TextExtractionResult(text=combined_text, pages=pages_dict, needs_ocr=False)

from .ocr_extractor import extract_text_with_ocr

def extract_document_text(file_path: str, file_type: str, perform_ocr_fallback: bool = True) -> TextExtractionResult:
    """Entry point for text extraction routing based on file type."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found on disk: {file_path}")
        
    if file_type.lower() == "pdf":
        result = extract_text_from_pdf(file_path)
        
        # Automatic OCR Fallback Pipeline
        if result.needs_ocr and perform_ocr_fallback:
            ocr_text, ocr_pages = extract_text_with_ocr(file_path)
            # Retain needs_ocr=True to log that OCR was heavily relied upon
            return TextExtractionResult(text=ocr_text, pages=ocr_pages, needs_ocr=True)
            
        return result
    elif file_type.lower() == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type for digital extraction: {file_type}")
