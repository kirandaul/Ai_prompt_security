#!/usr/bin/env python3
import json
import urllib.request
import time

API_URL = "http://127.0.0.1:3000/api/tester/bulk-scan"

# Just 50 test cases for quick validation
test_cases = [
    {"prompt": "SSN: 733-03-2530", "prompt_id": 304, "category": "PII", "expected_detector": "API_KEY_DETECTOR"},
    {"prompt": "Passport: P99331200", "prompt_id": 305, "category": "PII", "expected_detector": "API_KEY_DETECTOR"},
    {"prompt": "Connect to 192.168.1.1", "prompt_id": 902, "category": "INFRA", "expected_detector": "API_KEY_DETECTOR"},
    {"prompt": "Bank transfer: SWIFT code DEUTDEDD", "prompt_id": 551, "category": "COMPLIANCE", "expected_detector": "API_KEY_DETECTOR"},
    {"prompt": "; rm -rf /", "prompt_id": 700, "category": "ATTACK", "expected_detector": "SQL_INJECTION_DETECTOR"},
]

print(f"Running quick test with {len(test_cases)} cases...")

try:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(test_cases).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        
        results = result.get('results', [])
        passed = result.get('passed', 0)
        total = result.get('total', 0)
        
        print(f"\nResults: {passed}/{total} passed ({passed/total*100:.1f}%)\n")
        
        for r in results:
            status = "✓" if r['status'] == 'PASS' else "✗"
            print(f"{status} ID {r['prompt_id']} {r['category']:12} - Found: {r['detectors_found']}")

except Exception as e:
    print(f"Error: {e}")
