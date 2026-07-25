"""
CSV document parser.
Extracts text with row/column tracking.
"""

import csv
import io
from typing import Dict, List, Any
from .base_parser import BaseDocumentParser


class CSVParser(BaseDocumentParser):
    """Parse CSV documents."""
    
    async def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse CSV and extract with row/column information.
        
        Returns:
            {
                "success": bool,
                "filename": str,
                "file_type": "csv",
                "pages": [
                    {
                        "row": 1,
                        "columns": ["header1", "header2"],
                        "text": "value1 | value2",
                        "length": int
                    },
                    ...
                ],
                "total_pages": int,
                "text": "combined text",
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
            all_text = []
            
            # Parse CSV
            csv_file = io.StringIO(text)
            reader = csv.reader(csv_file)
            
            headers = None
            row_num = 0
            
            for row_data in reader:
                row_num += 1
                
                if row_num == 1:
                    headers = row_data
                    all_text.append(f"--- Headers ---\n{' | '.join(headers)}")
                
                # Filter out empty rows
                if not any(cell.strip() for cell in row_data):
                    continue
                
                row_text = " | ".join(row_data)
                pages.append({
                    "row": row_num,
                    "columns": headers if headers else [],
                    "values": row_data,
                    "text": row_text,
                    "length": len(row_text)
                })
                all_text.append(f"--- Row {row_num} ---\n{row_text}")
            
            # Extract metadata
            metadata = {
                "total_rows": row_num,
                "total_columns": len(headers) if headers else 0,
                "headers": headers if headers else [],
            }
            
            return {
                "success": True,
                "filename": filename,
                "file_type": "csv",
                "pages": pages,
                "total_pages": len(pages),
                "text": "\n".join(all_text),
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "file_type": "csv",
                "error": str(e),
                "pages": [],
                "total_pages": 0,
                "text": ""
            }
