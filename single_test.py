#!/usr/bin/env python3
import json
import urllib.request

API_URL = "http://127.0.0.1:3000/api/tester/scan"

test_case = {
    "prompt": "SSN: 733-03-2530",
    "prompt_id": 304,
    "category": "PII",
    "expected_detector": "API_KEY_DETECTOR"
}

print(f"Testing single case...")
print(f"Prompt: {test_case['prompt']}")

try:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(test_case).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        
        print(f"\nStatus: {result['status']}")
        print(f"Detectors found: {result['detectors_found']}")
        print(f"Expected: {result['expected_detector']}")
        
        # Check if it matches
        found = result['expected_detector'] in result['detectors_found']
        print(f"\nMatch: {'YES' if found else 'NO'}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
