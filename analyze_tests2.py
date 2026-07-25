import json

with open('test-data/prompts.json') as f:
    data = json.load(f)

# Analyze expected detectors per category
print('=== EXPECTED DETECTORS BY CATEGORY ===\n')

categories = {}
for c in data['cases']:
    cat = c.get('category', 'UNKNOWN')
    det = c.get('detector', 'UNKNOWN')
    
    if cat not in categories:
        categories[cat] = {}
    
    if det not in categories[cat]:
        categories[cat][det] = 0
    
    categories[cat][det] += 1

for cat in sorted(categories.keys()):
    print(f'\n{cat}:')
    for det in sorted(categories[cat].keys()):
        count = categories[cat][det]
        print(f'  {det:40} {count:4}')

# Show sample prompts for key patterns
print('\n=== SAMPLE PROMPTS FOR ANALYSIS ===\n')

for c in data['cases'][300:310]:
    print(f"{c['id']:4} {c['category']:12} -> {c['detector']:35}")
    print(f"      PROMPT: {c['prompt'][:80]}")
    print()
