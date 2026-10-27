import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

# NOTE FOR WINDOWS USERS:
# If Tesseract is not automatically found in your system PATH, uncomment and set the exact path:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_with_ocr(file_path: str) -> tuple[str, dict[int, str]]:
    """
    Converts a scanned PDF into images and extracts text using Tesseract OCR.
    Returns the combined text and a dictionary mapping page numbers to text.
    """
    try:
        # Note: Requires Poppler installed natively and added to PATH on Windows.
        images = convert_from_path(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images. Ensure Poppler is installed and in PATH. Error: {e}")
    
    full_text = []
    pages_dict = {}
    
    for i, image in enumerate(images):
        # Run optical character recognition on the current page image
        text = pytesseract.image_to_string(image)
        clean_text = text.strip()
        
        page_num = i + 1  # 1-indexed for accurate citations
        pages_dict[page_num] = clean_text
        full_text.append(clean_text)
        
    combined_text = "\n\n".join(full_text)
    return combined_text, pages_dict
