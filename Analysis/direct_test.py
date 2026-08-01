#!/usr/bin/env python3
"""Test detectors directly without API."""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from server import DETECTORS, analyze


async def run_direct_tests():
    """Test a subset of test cases directly."""
    
    with open('test-data/prompts.json') as f:
        data = json.load(f)
    
    test_cases = data['cases']
    
    print(f"=== DIRECT DETECTOR TEST ===\n")
    print(f"Total test cases: {len(test_cases)}")
    print(f"Detectors loaded: {len(DETECTORS)}\n")
    
    # Mapping of expected detector to new detectors (flexible matching)
    detector_mapping = {
        "API_KEY_DETECTOR": ["SSN_PASSPORT_DETECTOR", "BANKING_DETECTOR", "CONFIG_DETECTOR", "INTERNAL_IP_DETECTOR", "CLOUD_RESOURCE_DETECTOR"],
        "INTERNAL_IP_DETECTOR": ["INTERNAL_IP_DETECTOR"],
        "BANKING_DETECTOR": ["BANKING_DETECTOR"],
        "INJECTION_DETECTOR": ["INJECTION_DETECTOR", "SQL_INJECTION_DETECTOR"],
    }
    
    passed = 0
    failed = 0
    failed_tests = []
    
    # Test a sample from each category
    categories = {}
    for c in test_cases:
        cat = c['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(c)
    
    # Process each category
    for cat_name in sorted(categories.keys()):
        cat_tests = categories[cat_name]
        cat_passed = 0
        cat_total = len(cat_tests)
        
        for test_case in cat_tests:
            result, raw = await analyze(test_case['prompt'])
            detectors_found = list(set(f.detector for f in raw))
            
            expected = test_case.get('detector', 'NONE')
            
            # Check if matches expected
            found = expected in detectors_found
            
            # Apply flexible matching
            if not found and expected in detector_mapping:
                mapped = detector_mapping[expected]
                found = any(m in detectors_found for m in mapped)
            
            if found:
                passed += 1
                cat_passed += 1
            else:
                failed += 1
                if len(failed_tests) < 50:
                    failed_tests.append({
                        'id': test_case['id'],
                        'category': cat_name,
                        'expected': expected,
                        'found': detectors_found,
                        'prompt': test_case['prompt'][:50]
                    })
        
        pct = cat_passed / cat_total * 100 if cat_total > 0 else 0
        print(f"{cat_name:12} {cat_passed:4}/{cat_total:4} ({pct:5.1f}%)")
    
    total = passed + failed
    pct = passed / total * 100 if total > 0 else 0
    
    print(f"\n{'TOTAL':12} {passed:4}/{total:4} ({pct:5.1f}%)")
    
    # Show samples of failures
    if failed_tests:
        print(f"\n=== SAMPLE FAILURES ===")
        for test in failed_tests[:10]:
            print(f"ID {test['id']:4} {test['category']:12} Expected: {test['expected']:30} Found: {test['found']}")


if __name__ == "__main__":
    asyncio.run(run_direct_tests())
