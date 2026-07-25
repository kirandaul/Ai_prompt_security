import json

with open('test-data/prompts.json') as f:
    data = json.load(f)

# Show COMPLIANCE and INFRA samples
print("=== COMPLIANCE PATTERNS (expecting API_KEY_DETECTOR) ===\n")
count = 0
for c in data['cases']:
    if c['category'] == 'COMPLIANCE' and c['detector'] == 'API_KEY_DETECTOR' and count < 15:
        print(f"ID {c['id']:4}: {c['name']:30}")
        print(f"    PROMPT: {c['prompt']}")
        print()
        count += 1

print("\n=== INFRA PATTERNS (expecting API_KEY_DETECTOR) ===\n")
count = 0
for c in data['cases']:
    if c['category'] == 'INFRA' and c['detector'] == 'API_KEY_DETECTOR' and count < 15:
        print(f"ID {c['id']:4}: {c['name']:30}")
        print(f"    PROMPT: {c['prompt']}")
        print()
        count += 1
