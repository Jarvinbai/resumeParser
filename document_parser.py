# document_parser.py
import io
import os
from typing import BinaryIO, Optional

# PDF parsing
from PyPDF2 import PdfReader

# DOCX parsing
import docx

# Image parsing
import pytesseract
from PIL import Image

def extract_text_from_pdf(file: BinaryIO) -> str:
    """Extract text from a PDF file."""
    try:
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        print("Extracted Text From PDF:\n", text)
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(file: BinaryIO) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = docx.Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from DOCX: {str(e)}")

def extract_text_from_txt(file: BinaryIO) -> str:
    """Extract text from a TXT file."""
    try:
        content = file.read()
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='ignore')
        return content
    except Exception as e:
        raise Exception(f"Error extracting text from TXT: {str(e)}")

def extract_text_from_image(file: BinaryIO) -> str:
    """Extract text from an image using OCR."""
    try:
        image = Image.open(file)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")

def extract_text_from_file(file: BinaryIO, filename: str) -> str:
    """Extract text from a file based on its extension."""
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Reset file pointer to beginning
    file.seek(0)
    
    if file_ext in ['.pdf']:
        return extract_text_from_pdf(file)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file)
    elif file_ext in ['.txt']:
        return extract_text_from_txt(file)
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        return extract_text_from_image(file)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")