# document_parser.py
# Handles pulling text out of PDF and DOCX files.
# PyMuPDF for PDFs, python-docx for Word files.

import pymupdf
import docx


def extract_text_pdf(filepath):
    try:
        doc = pymupdf.open(filepath)
    except Exception as e:
        print(f"Could not open {filepath}: {e}")
        return None

    # Iterate pages and concatenate all text
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_docx(filepath):
    try:
        doc = docx.Document(filepath)
    except Exception as e:
        print(f"Could not open {filepath}: {e}")
        return None

    # Skip empty paragraphs (headers, footers, blank lines, etc.)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text(filepath):
    # Dispatch based on extension so callers don't have to care about file type
    if filepath.endswith(".pdf"):
        return extract_text_pdf(filepath)
    elif filepath.endswith(".docx"):
        return extract_text_docx(filepath)
    else:
        print(f"Unsupported file type: {filepath}")
        return None
