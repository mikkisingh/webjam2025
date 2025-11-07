"""
Text extraction utilities for medical bills.
Supports PDF and image files (JPG, PNG).
"""
import pdfplumber
from PIL import Image
import pytesseract
import os

class TextExtractor:
    """Extract text from various file formats."""
    
    @staticmethod
    def extract_from_pdf(file_path):
        """
        Extract text from a PDF file using pdfplumber.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return text.strip()
    
    @staticmethod
    def extract_from_image(file_path):
        """
        Extract text from an image file using Tesseract OCR.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text as a string
        """
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
    
    @staticmethod
    def extract_text(file_path, file_type):
        """
        Extract text from a file based on its type.
        
        Args:
            file_path: Path to the file
            file_type: Type of file ('pdf', 'jpg', 'png', 'jpeg')
            
        Returns:
            Extracted text as a string
        """
        file_type = file_type.lower()
        
        if file_type == 'pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif file_type in ['jpg', 'jpeg', 'png']:
            return TextExtractor.extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
