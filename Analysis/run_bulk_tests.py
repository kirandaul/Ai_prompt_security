#!/usr/bin/env python3
"""Run bulk tests via the API."""

import json
import urllib.request
import time

API_URL = "http://127.0.0.1:3000/api/tester/bulk-scan"
TEST_DATA_FILE = "test-data/prompts.json"


def run_bulk_tests():
    """Load test data and run all tests via the API."""
    
    print("Loading test data...")
    with open(TEST_DATA_FILE) as f:
        data = json.load(f)
    
    test_cases = data['cases']
    print(f"Loaded {len(test_cases)} test cases\n")
    
    # Prepare request payload
    payload = [
        {
            "prompt": c['prompt'],
            "prompt_id": c['id'],
            "prompt_name": c['name'],
            "category": c['category'],
            "expected_detector": c.get('detector', 'NONE'),
        }
        for c in test_cases
    ]
    
    print(f"Starting bulk scan of {len(payload)} cases...")
    start_time = time.time()
    
    try:
        # Create request
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        # Send request
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            elapsed = time.time() - start_time
            
            results = result.get('results', [])
            total = result.get('total', 0)
            passed = result.get('passed', 0)
            
            print(f"\n=== TEST RESULTS ===")
            print(f"Total: {total}")
            print(f"Passed: {passed}")
            print(f"Failed: {total - passed}")
            print(f"Pass Rate: {passed/total*100:.1f}%")
            print(f"Time: {elapsed:.2f}s ({elapsed/total*1000:.1f}ms per test)")
            
            # Show category breakdown
            print(f"\n=== BY CATEGORY ===")
            by_category = {}
            for r in results:
                cat = r.get('category', 'UNKNOWN')
                if cat not in by_category:
                    by_category[cat] = {'pass': 0, 'fail': 0}
                
                if r['status'] == 'PASS':
                    by_category[cat]['pass'] += 1
                else:
                    by_category[cat]['fail'] += 1
            
            for cat in sorted(by_category.keys()):
                stats = by_category[cat]
                total_cat = stats['pass'] + stats['fail']
                pct = stats['pass'] / total_cat * 100 if total_cat > 0 else 0
                print(f"{cat:12} {stats['pass']:3}/{total_cat:3} ({pct:5.1f}%)")
            
            # Show failed tests (first 20)
            failed = [r for r in results if r['status'] == 'FAIL']
            if failed:
                print(f"\n=== SAMPLE FAILURES (first 20 of {len(failed)}) ===")
                for r in failed[:20]:
                    print(f"ID {r['prompt_id']:4} {r['category']:12} -> "
                          f"Expected: {r['expected_detector']:30} "
                          f"Found: {r['detectors_found']}")

    except urllib.error.URLError as e:
        print(f"✗ Connection error: {e}")
        print("Make sure the backend is running: python -m uvicorn server:app --host 127.0.0.1 --port 3000")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_bulk_tests()
