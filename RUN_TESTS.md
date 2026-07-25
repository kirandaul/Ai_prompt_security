# 🧪 Running 1250 Enterprise Test Cases

## Quick Commands

### 1. Test a Single Case via API

```bash
curl -X POST http://127.0.0.1:3000/api/tester/scan \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "prompt": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
  "prompt_id": 1,
  "prompt_name": "OpenAI API Key",
  "category": "SECRET",
  "expected_detector": "API_KEY_DETECTOR"
}
EOF
```

**Expected Response:**
```json
{
  "status": "PASS",
  "detectors_found": ["API Key / Secret"],
  "duration_ms": 45.2
}
```

---

### 2. Load Test Cases in Python

```python
import json

# Load test data
with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

print(f"Loaded {data['total_cases']} test cases")
print(f"Generated: {data['generated_at']}")

# Access cases
cases = data['cases']
print(f"First case: {cases[0]['name']}")
```

---

### 3. Run Bulk Tests (First 50 Cases)

```python
import json
import requests
import time

# Load test data
with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

cases = data['cases'][:50]  # First 50 cases
results = {"passed": 0, "failed": 0, "total": len(cases)}

for case in cases:
    try:
        resp = requests.post(
            'http://127.0.0.1:3000/api/tester/scan',
            json={
                "prompt": case["prompt"],
                "prompt_id": case["id"],
                "expected_detector": case["detector"]
            },
            timeout=5
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if result['status'] == 'PASS':
                results['passed'] += 1
            else:
                results['failed'] += 1
    except:
        results['failed'] += 1

print(f"\n✅ {results['passed']} PASSED")
print(f"❌ {results['failed']} FAILED")
print(f"Pass Rate: {(results['passed']/results['total']*100):.1f}%")
```

---

### 4. Test All Categories

```python
import json

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

# Count by category
categories = {}
for case in data['cases']:
    cat = case['category']
    categories[cat] = categories.get(cat, 0) + 1

print("Test Case Distribution:")
for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}")
```

**Output:**
```
Test Case Distribution:
  ATTACK: 200
  COMPLIANCE: 150
  INFRA: 150
  PII: 250
  SAFE: 200
  SECRET: 300
```

---

### 5. Test Specific Detector

```python
import json
import requests

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

# Get all API_KEY_DETECTOR cases
api_key_cases = [c for c in data['cases'] if c['detector'] == 'API_KEY_DETECTOR']
print(f"Testing {len(api_key_cases)} API Key cases...")

passed = 0
for case in api_key_cases[:10]:  # Test first 10
    resp = requests.post(
        'http://127.0.0.1:3000/api/tester/scan',
        json={
            "prompt": case["prompt"],
            "prompt_id": case["id"],
            "expected_detector": case["detector"]
        }
    )
    if resp.json()['status'] == 'PASS':
        passed += 1

print(f"API_KEY_DETECTOR: {passed}/10 PASSED")
```

---

### 6. Performance Test (Measure Speed)

```python
import json
import requests
import time

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

cases = data['cases'][:100]  # First 100
durations = []

for case in cases:
    start = time.time()
    resp = requests.post(
        'http://127.0.0.1:3000/api/tester/scan',
        json={"prompt": case["prompt"]}
    )
    duration = (time.time() - start) * 1000
    durations.append(duration)

avg = sum(durations) / len(durations)
min_dur = min(durations)
max_dur = max(durations)

print(f"Performance: {avg:.2f}ms avg, {min_dur:.2f}ms min, {max_dur:.2f}ms max")
```

---

### 7. Accuracy Report (False Positives/Negatives)

```python
import json
import requests

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

tp = fp = tn = fn = 0

for case in data['cases']:
    resp = requests.post(
        'http://127.0.0.1:3000/api/tester/scan',
        json={"prompt": case["prompt"]}
    ).json()
    
    detected = len(resp['result']['findings']) > 0
    expected = case['expectedDetection']
    
    if detected and expected:
        tp += 1  # True positive
    elif detected and not expected:
        fp += 1  # False positive
    elif not detected and expected:
        fn += 1  # False negative
    elif not detected and not expected:
        tn += 1  # True negative

print(f"TP: {tp} | FP: {fp} | TN: {tn} | FN: {fn}")
print(f"Accuracy: {((tp+tn)/(tp+fp+tn+fn)*100):.1f}%")
print(f"Precision: {(tp/(tp+fp)*100):.1f}%")
print(f"Recall: {(tp/(tp+fn)*100):.1f}%")
```

---

## 📊 Test Case Statistics

```
Total Cases: 1,250

By Category:
  SECRET: 300 (24%) - API keys, passwords, credentials
  PII: 250 (20%) - Credit cards, personal info
  ATTACK: 200 (16%) - SQL injection, XSS, etc.
  COMPLIANCE: 150 (12%) - HIPAA, PCI-DSS, GDPR
  INFRA: 150 (12%) - Internal IPs, ARNs, configs
  SAFE: 200 (16%) - Negative tests (no secrets)

By Difficulty:
  Easy: ~450 (36%) - Basic patterns
  Medium: ~650 (52%) - Realistic scenarios
  Hard: ~150 (12%) - Edge cases and obfuscation

By Source:
  Developer: ~400
  DevOps: ~300
  Finance: ~200
  Security: ~200
  HR: ~100
  Healthcare: ~50
```

---

## 🎯 Common Test Scenarios

### Scenario 1: Validate All Detectors Work

```python
# Test one case per detector
import json
import requests

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

detectors = set(c['detector'] for c in data['cases'])

for detector in sorted(detectors):
    case = next(c for c in data['cases'] if c['detector'] == detector)
    resp = requests.post(
        'http://127.0.0.1:3000/api/tester/scan',
        json={"prompt": case["prompt"]}
    ).json()
    
    status = "✅" if resp['status'] == 'PASS' else "❌"
    print(f"{status} {detector}")
```

### Scenario 2: Test All Categories

```python
import json
import requests

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

categories = set(c['category'] for c in data['cases'])

for category in sorted(categories):
    cases = [c for c in data['cases'] if c['category'] == category]
    passed = 0
    
    for case in cases[:10]:  # Test first 10 of each
        resp = requests.post(
            'http://127.0.0.1:3000/api/tester/scan',
            json={"prompt": case["prompt"]}
        ).json()
        
        if resp['status'] == 'PASS' or (not case['expectedDetection'] and len(resp['result']['findings']) == 0):
            passed += 1
    
    print(f"{category}: {passed}/10 PASSED")
```

### Scenario 3: Stress Test (All 1250 Cases)

```bash
# This will take ~5-10 minutes depending on API speed

python << 'EOF'
import json
import requests
import time

with open('test-data/prompts.json', 'r') as f:
    data = json.load(f)

cases = data['cases']
passed = 0
failed = 0
errors = 0

start_time = time.time()

for i, case in enumerate(cases):
    try:
        resp = requests.post(
            'http://127.0.0.1:3000/api/tester/scan',
            json={"prompt": case["prompt"]},
            timeout=10
        ).json()
        
        if resp['status'] == 'PASS' or (not case['expectedDetection'] and len(resp['result']['findings']) == 0):
            passed += 1
        else:
            failed += 1
    except:
        errors += 1
    
    if (i+1) % 100 == 0:
        print(f"Tested {i+1}/{len(cases)}")

duration = time.time() - start_time

print(f"\n{'='*50}")
print(f"✅ PASSED: {passed}")
print(f"❌ FAILED: {failed}")
print(f"⚠️  ERRORS: {errors}")
print(f"⏱️  Duration: {duration/60:.1f} minutes")
print(f"📊 Pass Rate: {(passed/(passed+failed)*100):.1f}%")
print(f"⚡ Speed: {len(cases)/duration:.1f} requests/sec")
EOF
```

---

## 🔍 JSON Query Examples

### Find All Credit Card Tests

```bash
cat test-data/prompts.json | jq '.cases[] | select(.detector == "CREDIT_CARD_DETECTOR") | .name'
```

### Count by Difficulty

```bash
cat test-data/prompts.json | jq '[.cases[] | .difficulty] | group_by(.) | map({(.[0]): length})'
```

### Extract High Severity Cases

```bash
cat test-data/prompts.json | jq '.cases[] | select(.severity >= 90) | {name, severity, detector}'
```

---

## 📈 Expected Results

For a **well-tuned detector system**, expect:

- **Accuracy**: >95%
- **Precision**: >90%
- **Recall**: >90%
- **Response Time**: <100ms per test
- **Throughput**: >10 tests/sec

---

## 🚀 CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Load Test Cases
  run: |
    python -c "import json; d = json.load(open('test-data/prompts.json')); print(f'Loaded {d[\"total_cases\"]} cases')"

- name: Run Detector Tests
  run: |
    python run_tests.py

- name: Check Results
  run: |
    python -c "import json; r = json.load(open('test-results.json')); exit(0 if r['passed']/r['total'] > 0.95 else 1)"
```

---

**Total Test Cases**: 1,250
**Categories**: 6
**Difficulty Levels**: 3 (easy, medium, hard)
**Detectors Covered**: 14+
**Ready for Production**: ✅ Yes

