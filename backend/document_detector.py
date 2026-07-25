"""
Document detection system.
Scans uploaded documents for sensitive information.
"""

import base64
import os
from typing import Dict, List, Any
from document_parsers import BaseDocumentParser, MetadataExtractor


class DocumentDetector:
    """Main document detection orchestrator."""
    
    # Supported formats
    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'txt': 'text/plain',
    }
    
    # Max file size: 25 MB
    MAX_FILE_SIZE = 25 * 1024 * 1024
    
    def __init__(self, detectors: List = None):
        """
        Initialize document detector.
        
        Args:
            detectors: List of text detectors (e.g., from app.py)
        """
        self.detectors = detectors or []
    
    async def scan_document(
        self,
        document_base64: str,
        filename: str,
        document_type: str = None
    ) -> Dict[str, Any]:
        """
        Scan document for sensitive information.
        
        Args:
            document_base64: Base64 encoded document content
            filename: Original filename
            document_type: File type (pdf, docx, etc). Auto-detected if None.
            
        Returns:
            {
                "action": "ALLOW|BLOCK",
                "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                "totalFindings": int,
                "findings": [
                    {
                        "detector": "DETECTOR_NAME",
                        "reason": "What was detected",
                        "evidence": "The actual data found",
                        "location": "Page 2, Table 1",  # NEW
                        "severity": "HIGH",
                        "confidence": 0.99,
                        "file_location": {"type": "page", "value": 2}
                    },
                    ...
                ],
                "document_info": {
                    "filename": str,
                    "file_type": str,
                    "size_bytes": int,
                    "total_pages": int,
                    "parse_success": bool,
                    "parse_error": str (if failed)
                },
                "metadata_findings": [...],
                "summary": {
                    "total_findings": int,
                    "critical_count": int,
                    "high_count": int,
                    "medium_count": int,
                    "low_count": int,
                    "processing_time_ms": float
                }
            }
        """
        
        import time
        start_time = time.time()
        
        try:
            # Decode base64
            try:
                file_content = base64.b64decode(document_base64)
            except Exception as e:
                return {
                    "action": "ALLOW",
                    "severity": "LOW",
                    "error": f"Invalid base64 encoding: {str(e)}",
                    "findings": []
                }
            
            # Validate file size
            if len(file_content) > self.MAX_FILE_SIZE:
                return {
                    "action": "ALLOW",
                    "severity": "LOW",
                    "error": f"File too large: {len(file_content)} bytes (max {self.MAX_FILE_SIZE})",
                    "findings": []
                }
            
            # Determine file type
            if not document_type:
                document_type = self._detect_file_type(filename)
            
            if document_type not in self.SUPPORTED_FORMATS:
                return {
                    "action": "ALLOW",
                    "severity": "LOW",
                    "error": f"Unsupported file type: {document_type}",
                    "findings": [],
                    "document_info": {
                        "filename": filename,
                        "file_type": document_type,
                        "size_bytes": len(file_content),
                        "supported_formats": list(self.SUPPORTED_FORMATS.keys())
                    }
                }
            
            # Parse document
            parser = BaseDocumentParser.get_parser(document_type)
            parse_result = await parser.parse(file_content, filename)
            
            if not parse_result.get("success"):
                return {
                    "action": "ALLOW",
                    "severity": "LOW",
                    "error": parse_result.get("error", "Unknown parse error"),
                    "findings": [],
                    "document_info": {
                        "filename": filename,
                        "file_type": document_type,
                        "size_bytes": len(file_content),
                        "parse_success": False
                    }
                }
            
            # Extract text for scanning
            extracted_text = parse_result.get("text", "")
            metadata = parse_result.get("metadata", {})
            pages = parse_result.get("pages", [])
            
            print(f"DEBUG: Extracted text: {repr(extracted_text)}")
            print(f"DEBUG: Number of detectors: {len(self.detectors)}")
            
            # Scan text with all detectors
            findings = []
            for detector in self.detectors:
                try:
                    print(f"DEBUG: Running detector: {detector.name}")
                    detector_findings = await detector.detect(extracted_text)
                    print(f"DEBUG: {detector.name} found {len(detector_findings)} findings")
                    
                    # Enrich findings with document location
                    for finding in detector_findings:
                        # finding is a ThreatFinding object, not a dict
                        finding_text = finding.evidence if hasattr(finding, 'evidence') else finding.get("evidence", "")
                        location = self._find_location_in_pages(finding_text, pages)
                        
                        # Convert ThreatFinding to dict
                        finding_dict = {
                            "detector": finding.detector,
                            "reason": finding.category,
                            "evidence": finding.evidence,
                            "severity": self._severity_to_level(finding.severity),
                            "confidence": finding.confidence,
                            "location": location,
                            "file_location": self._get_file_location(location, document_type)
                        }
                        
                        findings.append(finding_dict)
                except Exception as e:
                    print(f"Error in {detector.__class__.__name__}: {str(e)}")
            
            # Scan metadata
            metadata_findings = MetadataExtractor.extract_metadata_findings(metadata)
            
            # Determine action and severity
            all_findings = findings + metadata_findings
            
            # Get highest severity
            severity = self._get_highest_severity(all_findings)
            action = "BLOCK" if all_findings else "ALLOW"
            
            # Count by severity
            severity_counts = self._count_by_severity(all_findings)
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "action": action,
                "severity": severity,
                "totalFindings": len(all_findings),
                "findings": findings,
                "metadata_findings": metadata_findings,
                "document_info": {
                    "filename": filename,
                    "file_type": document_type,
                    "size_bytes": len(file_content),
                    "total_pages": parse_result.get("total_pages", 0),
                    "parse_success": True
                },
                "metadata": metadata,
                "summary": {
                    "total_findings": len(all_findings),
                    "critical_count": severity_counts.get("CRITICAL", 0),
                    "high_count": severity_counts.get("HIGH", 0),
                    "medium_count": severity_counts.get("MEDIUM", 0),
                    "low_count": severity_counts.get("LOW", 0),
                    "processing_time_ms": round(processing_time, 2)
                }
            }
            
        except Exception as e:
            return {
                "action": "ALLOW",
                "severity": "LOW",
                "error": str(e),
                "findings": [],
                "document_info": {
                    "filename": filename,
                    "file_type": document_type,
                    "parse_success": False
                }
            }
    
    @staticmethod
    def _detect_file_type(filename: str) -> str:
        """Detect file type from filename."""
        if not filename:
            return "txt"
        
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return ext if ext else "txt"
    
    @staticmethod
    def _severity_to_level(severity: int) -> str:
        """Convert numeric severity (0-100) to level string."""
        if severity >= 90:
            return "CRITICAL"
        if severity >= 70:
            return "HIGH"
        if severity >= 40:
            return "MEDIUM"
        return "LOW"
    
    @staticmethod
    def _find_location_in_pages(search_text: str, pages: List[Dict]) -> str:
        """Find where text appears in pages."""
        if not search_text or not pages:
            return "Unknown location"
        
        search_lower = search_text.lower()
        
        for page in pages:
            page_text = page.get("text", "").lower()
            
            if search_lower in page_text:
                # Determine location type based on page structure
                if "page_num" in page:
                    return f"Page {page['page_num']}"
                elif "sheet" in page:
                    return f"{page['sheet']}[{page.get('cell', 'Unknown')}]"
                elif "section" in page:
                    return f"Section {page['section_num']} ({page['section']})"
                elif "row" in page:
                    return f"Row {page['row']}"
                elif "line" in page:
                    return f"Line {page['line']}"
        
        return "Document"
    
    @staticmethod
    def _get_file_location(location: str, file_type: str) -> Dict[str, Any]:
        """Parse location string into structured format."""
        import re
        
        if "Page" in location:
            match = re.search(r'Page (\d+)', location)
            if match:
                return {"type": "page", "value": int(match.group(1))}
        
        elif "[" in location and "]" in location:
            match = re.search(r'\[([A-Z0-9]+)\]', location)
            if match:
                return {"type": "cell", "value": match.group(1)}
        
        elif "Line" in location:
            match = re.search(r'Line (\d+)', location)
            if match:
                return {"type": "line", "value": int(match.group(1))}
        
        elif "Section" in location:
            match = re.search(r'Section (\d+)', location)
            if match:
                return {"type": "section", "value": int(match.group(1))}
        
        return {"type": "unknown", "value": location}
    
    @staticmethod
    def _get_highest_severity(findings: List[Dict]) -> str:
        """Get highest severity from findings."""
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        highest = "LOW"
        highest_score = 1
        
        for finding in findings:
            severity = finding.get("severity", "LOW").upper()
            score = severity_order.get(severity, 1)
            
            if score > highest_score:
                highest = severity
                highest_score = score
        
        return highest
    
    @staticmethod
    def _count_by_severity(findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for finding in findings:
            severity = finding.get("severity", "LOW").upper()
            if severity in counts:
                counts[severity] += 1
        
        return counts
