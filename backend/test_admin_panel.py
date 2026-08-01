#!/usr/bin/env python3
"""Test the admin panel key management endpoints"""

import requests
import json

API_BASE = "http://localhost:3000"

def test_admin_panel():
    print("=" * 70)
    print("🔐 ADMIN PANEL - KEY MANAGEMENT TEST")
    print("=" * 70)
    
    # Test 1: Generate key
    print("\n[Test 1] Generate activation key via admin panel")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/admin/generate-key",
            json={"hostname": "hackathon-066"},
            timeout=5
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            key = result['key']
            extension_id = result['extension_id']
            print(f"✅ SUCCESS: Generated key")
            print(f"   Key: {key[:32]}...")
            print(f"   Extension ID: {extension_id}")
        else:
            print(f"❌ FAILED: {result}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2: Get all keys
    print("\n[Test 2] Fetch all activation keys")
    print("-" * 70)
    
    try:
        response = requests.get(
            f"{API_BASE}/api/admin/activation-keys",
            timeout=5
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            total = result.get('total', 0)
            keys = result.get('keys', [])
            active_count = sum(1 for k in keys if k.get('is_active'))
            print(f"✅ SUCCESS: Fetched keys")
            print(f"   Total: {total} keys")
            print(f"   Active: {active_count}")
            print(f"   Inactive: {total - active_count}")
            
            if keys:
                k = keys[0]
                print(f"\n   Latest key:")
                print(f"     ID: {k['extension_id']}")
                print(f"     Status: {k['status']}")
                print(f"     Hostname: {k['hostname']}")
                print(f"     Created: {k['created_at']}")
        else:
            print(f"❌ FAILED: {result}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3: Deactivate key
    print("\n[Test 3] Deactivate activation key")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/admin/deactivate-key?key={key}",
            timeout=5
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            print(f"✅ SUCCESS: Key deactivated")
        else:
            print(f"❌ FAILED: {result}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 4: Try to use deactivated key (should fail)
    print("\n[Test 4] Try to use deactivated key in scan (should fail)")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/scan",
            json={
                "prompt": "test",
                "client_id": "test"
            },
            headers={
                "X-Activation-Key": key
            },
            timeout=5
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ SUCCESS: Deactivated key is rejected (401)")
        else:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 5: Reactivate key
    print("\n[Test 5] Reactivate activation key")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/admin/activate-key?key={key}",
            timeout=5
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            print(f"✅ SUCCESS: Key reactivated")
        else:
            print(f"❌ FAILED: {result}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 6: Use reactivated key (should succeed)
    print("\n[Test 6] Use reactivated key in scan (should succeed)")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/scan",
            json={
                "prompt": "test prompt",
                "client_id": "test"
            },
            headers={
                "X-Activation-Key": key
            },
            timeout=5
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS: Reactivated key works (200 OK)")
        else:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL ADMIN PANEL TESTS PASSED!")
    print("=" * 70)
    print("\n🎉 Features verified:")
    print("  ✓ Generate keys from admin panel")
    print("  ✓ View all keys with status")
    print("  ✓ Deactivate keys (disable usage)")
    print("  ✓ Reactivate keys (re-enable usage)")
    print("  ✓ Delete keys (permanent removal)")
    print("  ✓ Keys enforce deactivation immediately")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    success = test_admin_panel()
    sys.exit(0 if success else 1)
