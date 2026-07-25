"""
Extract and scan metadata from documents for sensitive information.
"""

from typing import Dict, List, Any


class MetadataExtractor:
    """Extract and analyze metadata."""
    
    @staticmethod
    def extract_metadata_findings(metadata: Dict[str, Any]) -> List[str]:
        """
        Scan metadata for potentially sensitive information.
        
        Returns list of sensitive metadata fields found.
        """
        sensitive_findings = []
        
        sensitive_fields = [
            'author', 'creator', 'title', 'subject', 'comments',
            'category', 'company', 'manager', 'owner'
        ]
        
        for key, value in metadata.items():
            if not value:
                continue
            
            key_lower = str(key).lower()
            value_str = str(value).strip()
            
            # Check if field is sensitive
            if any(field in key_lower for field in sensitive_fields):
                if value_str and len(value_str) > 0:
                    sensitive_findings.append({
                        "field": key,
                        "value": value_str,
                        "type": "metadata",
                        "reason": f"Potentially sensitive metadata: {key}"
                    })
        
        return sensitive_findings
    
    @staticmethod
    def redact_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive metadata fields."""
        redact_fields = [
            'author', 'creator', 'title', 'subject', 'comments',
            'category', 'company', 'manager', 'owner', 'created',
            'modified', 'creation_date', 'modification_date'
        ]
        
        redacted = {}
        for key, value in metadata.items():
            key_lower = str(key).lower()
            if any(field in key_lower for field in redact_fields):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        
        return redacted
