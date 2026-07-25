"""
Plain text document parser.
Extracts text with line tracking.
"""

from typing import Dict, List, Any
from .base_parser import BaseDocumentParser


class TXTParser(BaseDocumentParser):
    """Parse TXT documents."""
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse TXT and extract with line information.
        
        Returns:
            {
                "success": bool,
                "filename": str,
                "file_type": "txt",
                "pages": [
                    {
                        "line": 1,
                        "text": "...",
                        "length": int
                    },
                    ...
                ],
                "total_pages": int,  # Total lines
                "text": "full content",
                "metadata": {...}
            }
        """
        
        try:
            # Detect encoding
            try:
                text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    text = file_content.decode('iso-8859-1')
            
            pages = []
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                
                # Skip empty lines but include them in count
                if line:
                    pages.append({
                        "line": line_num,
                        "text": line,
                        "length": len(line)
                    })
            
            # Extract metadata
            metadata = {
                "total_lines": len(lines),
                "total_characters": len(text),
                "file_size_bytes": len(file_content),
            }
            
            return {
                "success": True,
                "filename": filename,
                "file_type": "txt",
                "pages": pages,
                "total_pages": len(pages),
                "text": text,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "file_type": "txt",
                "error": str(e),
                "pages": [],
                "total_pages": 0,
                "text": ""
            }
