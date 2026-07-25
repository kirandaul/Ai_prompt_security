"""
Document parsing module for extracting text from various file formats.
Supports: PDF, DOCX, XLSX, CSV, TXT
"""

from .base_parser import BaseDocumentParser
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .xlsx_parser import XLSXParser
from .csv_parser import CSVParser
from .txt_parser import TXTParser
from .metadata_extractor import MetadataExtractor

__all__ = [
    'BaseDocumentParser',
    'PDFParser',
    'DOCXParser',
    'XLSXParser',
    'CSVParser',
    'TXTParser',
    'MetadataExtractor',
]
