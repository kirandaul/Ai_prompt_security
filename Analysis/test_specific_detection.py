#!/usr/bin/env python3
"""
Test what's being detected in the specific message
"""

import requests
import json

BASE_URL = "http://localhost:3000"

# Get a test key
response = requests.post(f"{BASE_URL}/api/admin/generate-key", json={"hostname": "test"})
key = response.json().get('key')

print(f"Using key: {key[:16]}...\n")

test_messages = [
    "my aws server is not working what should i do",
    "my aws server is not working",
    "AWS Secret",
    "If you're using the uv package manager",
    "You can also run",
    "If dependencies are already installed",
    "Then open",
    "If you just want to serve static files with Python",
]

for msg in test_messages:
    print(f"\n{'='*70}")
    print(f"Testing: '{msg}'")
    print('='*70)
    
    r = requests.post(
        f"{BASE_URL}/api/scan",
        json={
            "prompt": msg,
            "client_id": "test",
            "source": "test"
        },
        headers={"X-Activation-Key": key}
    )
    
    data = r.json()
    
    print(f"Severity: {data.get('severity')}")
    print(f"Action: {data.get('action')}")
    
    findings = data.get('findings', [])
    if findings:
        print(f"Findings: {len(findings)}")
        for f in findings[:3]:
            print(f"  - {f.get('type')}: {f.get('value')[:50] if f.get('value') else 'N/A'}")
    else:
        print("Findings: None (SAFE)")
