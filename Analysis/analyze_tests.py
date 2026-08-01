import json

with open('test-data/prompts.json') as f:
    data = json.load(f)

# Count by category
cats = {}
for c in data['cases']:
    cat = c.get('category', 'UNKNOWN')
    cats[cat] = cats.get(cat, 0) + 1

print('=== CATEGORY DISTRIBUTION ===')
for cat, count in sorted(cats.items()):
    print(f'{cat:15} {count:4}')

print('\n=== SAMPLE NON-SECRET CASES ===')
count = 0
for c in data['cases']:
    if c['category'] not in ['SECRET', 'SAFE'] and count < 20:
        print(f"ID {c['id']:4} {c['category']:12} -> {c['detector']:35} : {c['name']}")
        count += 1
