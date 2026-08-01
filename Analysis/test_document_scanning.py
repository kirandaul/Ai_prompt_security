#!/usr/bin/env python3
"""
Test Document Scanning with Activation Key
"""

import requests
import base64
import json

BASE_URL = "http://localhost:3000"

def get_test_key():
    """Get an active test key"""
    try:
        response = requests.post(f"{BASE_URL}/api/admin/generate-key", json={"hostname": "test-doc"})
        if response.status_code == 200:
            return response.json().get('key')
    except:
        pass
    return None


def test_document_with_key(key):
    """Test document scanning"""
    print("\n" + "="*60)
    print("TEST: Document Scanning With Key")
    print("="*60)
    
    # Create a simple test document (base64 encoded)
    test_content = """
    CONFIDENTIAL DOCUMENT
    
    My credit card: 4532-1111-2222-3333
    My AWS Key: AKIAIOSFODNN7EXAMPLE
    My API Key: sk-1234567890abcdefghij
    Email: john.doe@company.com
    Phone: +1-555-0123
    
    PAN: BTKPD9226K
    """
    
    doc_bytes = test_content.encode('utf-8')
    doc_base64 = base64.b64encode(doc_bytes).decode('utf-8')
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan-document",
            json={
                "document": doc_base64,
                "filename": "test.txt",
                "document_type": "text/plain",
                "client_id": "test-client",
                "source": "test"
            },
            headers={"X-Activation-Key": key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Severity: {data.get('severity')}")
            print(f"✅ Action: {data.get('action')}")
            print(f"✅ Total Findings: {data.get('totalFindings')}")
            print(f"✅ Document Info: {data.get('document_info')}")
            
            findings = data.get('findings', [])
            if findings:
                print(f"\n📋 Findings ({len(findings)}):")
                for i, finding in enumerate(findings[:5], 1):
                    print(f"  {i}. {finding.get('type')} - {finding.get('severity')} - {finding.get('value', 'N/A')[:30]}")
            
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_document_without_key():
    """Test document scanning without key (should fail)"""
    print("\n" + "="*60)
    print("TEST: Document Scanning Without Key (Should Fail)")
    print("="*60)
    
    test_content = "My AWS Key: AKIAIOSFODNN7EXAMPLE"
    doc_bytes = test_content.encode('utf-8')
    doc_base64 = base64.b64encode(doc_bytes).decode('utf-8')
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan-document",
            json={
                "document": doc_base64,
                "filename": "test.txt",
                "document_type": "text/plain",
                "client_id": "test-client",
                "source": "test"
            }
        )
        
        if response.status_code == 401:
            print(f"✅ Status: {response.status_code} (Correctly Rejected)")
            return True
        else:
            print(f"❌ Status: {response.status_code} (Should be 401)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 DOCUMENT SCANNING TEST SUITE")
    
    key = get_test_key()
    if not key:
        print("❌ Failed to generate test key")
        exit(1)
    
    print(f"\n✅ Test Key Generated: {key[:16]}...")
    
    results = {}
    results['Document With Key'] = test_document_with_key(key)
    results['Document Without Key'] = test_document_without_key()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL DOCUMENT TESTS PASSED! 🎉")
