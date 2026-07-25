"""
Base class for all document parsers.
Defines interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import io


class BaseDocumentParser(ABC):
    """Base class for document parsers."""
    
    def __init__(self):
        self.file_content = None
        self.filename = None
    
    @abstractmethod
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse document and extract text with location information.
        
        Args:
            file_content: Document bytes
            filename: Original filename
            
        Returns:
            {
                "success": bool,
                "filename": str,
                "file_type": str,
                "pages": [...],
                "total_pages": int,
                "text": str,  # All text combined
                "metadata": {...},
                "error": str (if failed)
            }
        """
        pass
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract plain text from document."""
        raise NotImplementedError
    
    def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """Extract metadata from document."""
        return {}
    
    @staticmethod
    def get_parser(file_type: str) -> 'BaseDocumentParser':
        """Get appropriate parser for file type."""
        from .pdf_parser import PDFParser
        from .docx_parser import DOCXParser
        from .xlsx_parser import XLSXParser
        from .csv_parser import CSVParser
        from .txt_parser import TXTParser
        
        parsers = {
            'pdf': PDFParser,
            'docx': DOCXParser,
            'xlsx': XLSXParser,
            'csv': CSVParser,
            'txt': TXTParser,
        }
        
        parser_class = parsers.get(file_type.lower())
        if not parser_class:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return parser_class()
