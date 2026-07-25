"""
PDF document parser using pypdf library.
Extracts text with page-level tracking.
"""

import io
from typing import Dict, List, Any
from .base_parser import BaseDocumentParser

try:
    import pypdf
except ImportError:
    pypdf = None


class PDFParser(BaseDocumentParser):
    """Parse PDF documents and extract text."""
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse PDF and extract text with page information.
        
        Returns:
            {
                "success": bool,
                "filename": str,
                "file_type": "pdf",
                "pages": [
                    {
                        "page_num": 1,
                        "text": "...",
                        "length": int
                    },
                    ...
                ],
                "total_pages": int,
                "text": "combined text",
                "metadata": {...}
            }
        """
        
        if not pypdf:
            return {
                "success": False,
                "error": "pypdf library not installed",
                "filename": filename,
                "file_type": "pdf"
            }
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            total_pages = len(pdf_reader.pages)
            pages = []
            all_text = []
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append({
                            "page_num": page_num,
                            "text": page_text,
                            "length": len(page_text)
                        })
                        all_text.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as e:
                    pages.append({
                        "page_num": page_num,
                        "text": "",
                        "error": str(e),
                        "length": 0
                    })
            
            # Extract metadata
            metadata = {}
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                    "modification_date": str(pdf_reader.metadata.get("/ModDate", "")),
                }
            
            return {
                "success": True,
                "filename": filename,
                "file_type": "pdf",
                "pages": pages,
                "total_pages": total_pages,
                "text": "\n".join(all_text),
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "file_type": "pdf",
                "error": str(e),
                "pages": [],
                "total_pages": 0,
                "text": ""
            }
