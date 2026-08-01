#!/usr/bin/env python3
"""
End-to-End Test Suite
Tests complete flow: key generation → dashboard → activation
"""

import requests
import json
import time

BASE_URL = "http://localhost:3000"

def test_key_generation():
    """Test: Generate activation key"""
    print("\n" + "="*60)
    print("TEST 1: Generate Activation Key")
    print("="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/api/admin/generate-key", json={
            "hostname": "test-device-001"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Status Field: {data.get('status')}")
            print(f"✅ Key Generated: {data.get('key', 'N/A')[:16]}..." if data.get('key') else "❌ No key")
            print(f"✅ Extension ID: {data.get('extension_id')}")
            
            if data.get('key') and len(data.get('key', '')) == 64:
                print("✅ Key format valid (64 characters)")
                return data.get('key')
            else:
                print(f"❌ Key invalid: {len(data.get('key', ''))} chars")
                return None
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_get_all_keys():
    """Test: Retrieve all activation keys"""
    print("\n" + "="*60)
    print("TEST 2: Get All Activation Keys")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/admin/activation-keys")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            keys = data.get('keys', [])
            print(f"✅ Total Keys: {len(keys)}")
            
            if keys:
                print(f"\nKey Summary:")
                for i, key in enumerate(keys[-3:], 1):  # Show last 3
                    print(f"  {i}. Status: {key.get('status')} | Hostname: {key.get('hostname')} | Created: {key.get('created_at', 'N/A')[:10]}")
            
            return len(keys) > 0
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scan_with_key(key):
    """Test: Scan with valid key"""
    print("\n" + "="*60)
    print("TEST 3: Scan Text With Activation Key")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan",
            json={
                "prompt": "My AWS key is AKIAIOSFODNN7EXAMPLE",
                "client_id": "test-client",
                "source": "test"
            },
            headers={"X-Activation-Key": key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code} (Authorized)")
            print(f"✅ Severity: {data.get('severity')}")
            print(f"✅ Action: {data.get('action')}")
            print(f"✅ Findings: {data.get('totalFindings')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scan_without_key():
    """Test: Scan without key (should fail)"""
    print("\n" + "="*60)
    print("TEST 4: Scan Without Key (Should Fail)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan",
            json={
                "prompt": "My AWS key is AKIAIOSFODNN7EXAMPLE",
                "client_id": "test-client",
                "source": "test"
            }
        )
        
        if response.status_code == 401:
            print(f"✅ Status: {response.status_code} (Correctly Rejected)")
            print(f"✅ Response: {response.json().get('detail', 'Unauthorized')}")
            return True
        else:
            print(f"❌ Status: {response.status_code} (Should be 401)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_deactivate_key(key):
    """Test: Deactivate activation key"""
    print("\n" + "="*60)
    print("TEST 5: Deactivate Key")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/deactivate-key?key={key}",
            json={}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scan_with_deactivated_key(key):
    """Test: Scan with deactivated key (should fail)"""
    print("\n" + "="*60)
    print("TEST 6: Scan With Deactivated Key (Should Fail)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan",
            json={
                "prompt": "My AWS key is AKIAIOSFODNN7EXAMPLE",
                "client_id": "test-client",
                "source": "test"
            },
            headers={"X-Activation-Key": key}
        )
        
        if response.status_code == 401:
            print(f"✅ Status: {response.status_code} (Correctly Rejected)")
            return True
        else:
            print(f"❌ Status: {response.status_code} (Should be 401)")
            print(f"Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_reactivate_key(key):
    """Test: Reactivate key"""
    print("\n" + "="*60)
    print("TEST 7: Reactivate Key")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/activate-key?key={key}",
            json={}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scan_with_reactivated_key(key):
    """Test: Scan with reactivated key (should work)"""
    print("\n" + "="*60)
    print("TEST 8: Scan With Reactivated Key (Should Work)")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scan",
            json={
                "prompt": "My AWS key is AKIAIOSFODNN7EXAMPLE",
                "client_id": "test-client",
                "source": "test"
            },
            headers={"X-Activation-Key": key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code} (Authorized)")
            print(f"✅ Severity: {data.get('severity')}")
            return True
        else:
            print(f"❌ Status: {response.status_code} (Should be 200)")
            print(f"Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 RUNNING END-TO-END TEST SUITE 🧪")
    print("="*60)
    
    results = {}
    
    # Test 1: Generate key
    key = test_key_generation()
    results['Generate Key'] = key is not None
    
    if not key:
        print("\n❌ Cannot continue without key")
        return results
    
    # Test 2: Get all keys
    results['Get All Keys'] = test_get_all_keys()
    
    # Test 3: Scan with key
    results['Scan With Key'] = test_scan_with_key(key)
    
    # Test 4: Scan without key
    results['Scan Without Key'] = test_scan_without_key()
    
    # Test 5: Deactivate key
    results['Deactivate Key'] = test_deactivate_key(key)
    
    # Test 6: Scan with deactivated key
    results['Scan With Deactivated Key'] = test_scan_with_deactivated_key(key)
    
    # Test 7: Reactivate key
    results['Reactivate Key'] = test_reactivate_key(key)
    
    # Test 8: Scan with reactivated key
    results['Scan With Reactivated Key'] = test_scan_with_reactivated_key(key)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return results


if __name__ == "__main__":
    run_all_tests()
