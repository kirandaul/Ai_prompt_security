#!/usr/bin/env python3
"""Test a few samples to verify detectors are working."""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from server import analyze


async def test_samples():
    test_cases = [
        # PII - SSN
        {
            "prompt": "SSN: 733-03-2530",
            "expected": "SSN_PASSPORT_DETECTOR",
            "category": "PII"
        },
        # PII - Passport
        {
            "prompt": "Passport: P99331200",
            "expected": "SSN_PASSPORT_DETECTOR",
            "category": "PII"
        },
        # COMPLIANCE - Banking SWIFT
        {
            "prompt": "Bank transfer: SWIFT code DEUTDEDD",
            "expected": "BANKING_DETECTOR",
            "category": "COMPLIANCE"
        },
        # COMPLIANCE - Routing
        {
            "prompt": "Routing number: 021000021",
            "expected": "BANKING_DETECTOR",
            "category": "COMPLIANCE"
        },
        # INFRA - Internal IP
        {
            "prompt": "Connect to 192.168.119.216",
            "expected": "INTERNAL_IP_DETECTOR",
            "category": "INFRA"
        },
        # INFRA - Config
        {
            "prompt": "postgresql://admin:SecurePass@db.internal:5432/production",
            "expected": "CONFIG_DETECTOR",
            "category": "INFRA"
        },
        # ATTACK - Command Injection
        {
            "prompt": "; rm -rf /",
            "expected": "INJECTION_DETECTOR",
            "category": "ATTACK"
        },
    ]
    
    print("=== TESTING SAMPLE CASES ===\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result, raw = await analyze(test['prompt'])
        detectors_found = list(set(f.detector for f in raw))
        
        # Check if expected detector found
        found = test['expected'] in detectors_found or any(
            test['expected'].lower() in d.lower() for d in detectors_found
        )
        
        status = "✓ PASS" if found else "✗ FAIL"
        
        if found:
            passed += 1
        else:
            failed += 1
        
        print(f"{i}. {test['category']:12} {status}")
        print(f"   Prompt: {test['prompt'][:60]}")
        print(f"   Expected: {test['expected']}")
        print(f"   Found: {detectors_found}")
        print()
    
    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print(f"Pass Rate: {passed/len(test_cases)*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(test_samples())
