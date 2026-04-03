# loader.py
import fitz  # PyMuPDF

def load_pdf(pdf_path: str) -> str:
    """
    Load PDF and return raw extracted text.
    This should be called ONCE.
    """
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text() + "\n"

    return full_text
