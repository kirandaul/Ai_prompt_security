#!/usr/bin/env python3
"""
Test document scanning directly.
"""

import asyncio
import base64
from document_detector import DocumentDetector
from detectors.pan_detector import PanDetector


async def test_doc_scan():
    # Create detectors list
    detectors = [PanDetector()]
    
    # Create document detector
    doc_detector = DocumentDetector(detectors=detectors)
    
    # Create test document content
    content = "My Pan Number is BTKPD9226K"
    content_bytes = content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
    
    print(f"Original content: {content}")
    print(f"Content bytes: {content_bytes}")
    print(f"Base64: {content_base64[:50]}...")
    
    # Scan document
    result = await doc_detector.scan_document(
        document_base64=content_base64,
        filename="test.txt",
        document_type="txt"
    )
    
    print(f"\nResult:")
    print(f"  Action: {result['action']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Total Findings: {result['totalFindings']}")
    print(f"  Findings: {result['findings']}")
    
    if result['findings']:
        for f in result['findings']:
            print(f"    - {f['detector']}: {f.get('evidence')}")


if __name__ == "__main__":
    asyncio.run(test_doc_scan())
