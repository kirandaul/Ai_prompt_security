#!/usr/bin/env python3
"""Quick synchronous test."""

import json

print("Loading test data...")
with open('test-data/prompts.json') as f:
    data = json.load(f)

test_cases = data['cases']
print(f"Total: {len(test_cases)} test cases")

# Count by category
cats = {}
for c in test_cases:
    cat = c['category']
    det = c['detector']
    if cat not in cats:
        cats[cat] = {}
    if det not in cats[cat]:
        cats[cat][det] = 0
    cats[cat][det] += 1

print("\n=== EXPECTED DETECTORS BY CATEGORY ===\n")
for cat in sorted(cats.keys()):
    print(f"{cat}:")
    for det in sorted(cats[cat].keys()):
        count = cats[cat][det]
        print(f"  {det:35} {count:3}")

print("\n✓ Test data loaded successfully!")
