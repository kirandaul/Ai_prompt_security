#!/usr/bin/env python3
"""Test the /api/scan-document endpoint"""

import base64
import requests
import json

def test_scan_document():
    # Test with PAN
    content = b"My Pan Number is BTKPD9226K"
    b64 = base64.b64encode(content).decode()
    
    payload = {
        "document": b64,
        "filename": "test_pan.txt",
        "document_type": "txt"
    }
    
    print("Testing /api/scan-document endpoint...")
    print(f"Payload: {json.dumps({'filename': payload['filename'], 'document_type': payload['document_type']}, indent=2)}")
    
    try:
        resp = requests.post('http://localhost:3000/api/scan-document', json=payload, timeout=10)
        print(f"\nStatus Code: {resp.status_code}")
        
        result = resp.json()
        print(f"\nResponse:\n{json.dumps(result, indent=2)}")
        
        if result.get('totalFindings', 0) > 0:
            print("\n✅ SUCCESS: Found PAN number!")
        else:
            print("\n❌ FAILED: No findings detected")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scan_document()
