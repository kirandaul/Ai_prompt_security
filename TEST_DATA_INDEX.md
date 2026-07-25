# 📚 Test Data Index - 1,250 Enterprise Security Test Cases

## 🎯 Quick Links

| Document | Purpose | Format |
|----------|---------|--------|
| **test-data/prompts.json** | 1,250 test cases | JSON (0.49 MB) |
| **TEST_DATA_README.md** | Complete documentation | Markdown |
| **RUN_TESTS.md** | Testing examples & scripts | Markdown + Code |
| **TEST_DATA_SUMMARY.txt** | Quick reference | Text |
| **generate_test_cases.py** | Generator script | Python |

---

## 📊 Test Data Overview

```
Total Cases: 1,250

SECRET:      300 (24%)  - API keys, passwords, credentials
PII:         250 (20%)  - Credit cards, personal info
ATTACK:      200 (16%)  - SQL injection, XSS, etc.
COMPLIANCE:  150 (12%)  - HIPAA, PCI-DSS, GDPR, SOX
INFRA:       150 (12%)  - Internal IPs, ARNs, configs
SAFE:        200 (16%)  - Negative tests (no secrets)
```

---

## 🚀 Getting Started

### 1. **Load Test Cases**
```python
import json
with open('test-data/prompts.json') as f:
    data = json.load(f)
print(f"Loaded {data['total_cases']} cases")
```

### 2. **Run a Quick Test**
```bash
curl -X POST http://127.0.0.1:3000/api/tester/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt":"sk-proj-abc..."}'
```

### 3. **Run Test Script**
See **RUN_TESTS.md** for:
- Single test execution
- Bulk testing
- Performance benchmarking
- Accuracy reporting

---

## 📋 Test Categories

### 🔑 SECRETS (300 cases)

**Include:**
- OpenAI keys (sk-proj-*, sk-*)
- GitHub PAT (ghp_*, github_pat_*)
- AWS access keys (AKIA*)
- AWS secret keys
- Passwords (password=...)
- JWT tokens
- Private keys (PEM, OpenSSH)
- DB connection strings
- OAuth client secrets
- Azure/GCP API keys
- Slack/Discord webhooks
- Basic Auth headers
- Docker Registry tokens
- Terraform state secrets

**Detectors Used:**
- API_KEY_DETECTOR
- AWS_SECRET_DETECTOR
- PASSWORD_DETECTOR
- JWT_DETECTOR
- PRIVATE_KEY_DETECTOR

---

### 👤 PII (250 cases)

**Include:**
- Credit cards (Visa, MasterCard, Amex, Discover)
- Credit card + CVV + Expiry
- PAN (India)
- Aadhaar (India)
- Email addresses
- Phone numbers (India/International)
- Social Security Number
- Passport number
- Bank account / IBAN / SWIFT
- Cryptocurrency wallets

**Detectors Used:**
- CREDIT_CARD_DETECTOR
- PAN_DETECTOR
- AADHAAR_DETECTOR
- EMAIL_DETECTOR
- PHONE_DETECTOR

---

### 💳 BANKING & FINANCIAL (50 cases)

**Include:**
- Full credit card with CVV/expiry
- IBAN codes
- SWIFT codes
- Routing numbers
- Bank account numbers
- Financial transactions
- Trading credentials

**Coverage:**
- PCI-DSS compliance data
- Payment card industry standards
- International banking formats

---

### ⚖️ COMPLIANCE (150 cases)

**HIPAA (Healthcare)** - 20 cases
- Patient MRN
- Diagnosis information
- Medication details
- Medical history

**PCI-DSS (Payments)** - 50 cases
- Credit card + CVV
- Payment authentication
- Card holder data

**GDPR (EU)** - 30 cases
- Name + Email + Phone combinations
- Personal data combinations
- Consent tracking

**SOX (Financial)** - 20 cases
- Audit logs
- Financial statements
- Revenue/expense data

**Healthcare General** - 20 cases
- Health conditions
- Insurance info
- Treatment plans

---

### ⚔️ ATTACKS (200 cases)

**SQL Injection** - 40 cases
- UNION SELECT
- OR 1=1
- Comment-based injection
- Blind injection

**XSS** - 40 cases
- Script tags
- Event handlers (onerror, onload, onclick)
- JavaScript URIs
- SVG/iframe payloads

**Prompt Injection** - 40 cases
- Override instructions
- System prompt attacks
- Jailbreak attempts

**Command Injection** - 20 cases
- Shell command execution
- Command chaining
- Path traversal

**LDAP Injection** - 15 cases
- Directory traversal
- Filter manipulation

**NoSQL Injection** - 15 cases
- MongoDB injection
- DynamoDB attacks

**Jailbreak** - 30 cases
- LLM jailbreak patterns
- Constraint bypass

---

### 🏢 INFRASTRUCTURE (150 cases)

**Internal IPs** - 20 cases
- 192.168.x.x
- 10.x.x.x
- 172.16-31.x.x

**Cloud Identifiers** - 40 cases
- AWS ARN
- Azure resource IDs
- GCP resource paths

**Internal URLs** - 20 cases
- Internal domains
- Internal APIs
- Admin panels

**Configuration** - 30 cases
- Database hosts/ports
- API endpoints
- Server metadata

**Kubernetes/Docker** - 40 cases
- Secret specs
- Credentials
- Registry configs

---

### ✅ SAFE (200 cases - Negative Tests)

**Purpose:** Test that legitimate text does NOT trigger false positives

**Include:**
- Security best practices questions
- API documentation
- Code examples
- Educational content
- Format specifications

**Examples:**
- "What is the best way to handle API authentication?"
- "How do I securely store passwords?"
- "Explain JWT token structure"

---

## 📈 Test Case Attributes

Each test case includes:

```json
{
  "id": 1,                                    // Unique ID
  "name": "Test Name",                        // Display name
  "category": "SECRET|PII|ATTACK|etc",       // Category
  "detector": "DETECTOR_NAME",                // Expected detector
  "severity": 0-100,                          // Severity level
  "expectedDetection": true|false,            // Should trigger?
  "difficulty": "easy|medium|hard",           // Test difficulty
  "tags": ["tag1", "tag2"],                   // Search tags
  "source": "developer|devops|etc",           // Source context
  "format": "text|json|yaml|code|log",        // Prompt format
  "prompt": "actual test prompt"               // Test data
}
```

---

## 🎯 Usage Scenarios

### Scenario 1: Regression Testing
```
Run all 1250 cases
Assert >95% pass rate
Track results over time
```

### Scenario 2: CI/CD Integration
```
Load test data
Run against API
Fail if pass rate < 90%
Auto-generate report
```

### Scenario 3: Performance Benchmarking
```
Measure each detector
Identify slowdowns
Optimize patterns
Track improvements
```

### Scenario 4: Compliance Validation
```
Verify HIPAA coverage
Check PCI-DSS detection
Validate GDPR patterns
Ensure SOX compliance
```

### Scenario 5: Detector Comparison
```
Compare detector accuracy
Test edge cases
Validate severity levels
Measure precision/recall
```

---

## 📊 Expected Results

### Accuracy Metrics
- **Accuracy**: >95% (correct classifications)
- **Precision**: >90% (low false positives)
- **Recall**: >90% (catches real issues)
- **F1 Score**: >90% (overall balance)

### Performance Metrics
- **Response Time**: <100ms per test
- **Throughput**: >10 tests/sec
- **P99 Latency**: <200ms
- **Total Time**: <10 minutes for all 1,250

### Detection Rates
- **True Positives**: >1,150 (good detections)
- **True Negatives**: >150 (correct non-detections)
- **False Positives**: <15 (over-detection)
- **False Negatives**: <10 (missed detections)

---

## 🔍 Search & Filter

### Filter by Category
```python
cases = [c for c in data['cases'] if c['category'] == 'SECRET']
```

### Filter by Detector
```python
cases = [c for c in data['cases'] if c['detector'] == 'API_KEY_DETECTOR']
```

### Filter by Difficulty
```python
cases = [c for c in data['cases'] if c['difficulty'] == 'hard']
```

### Filter by Source
```python
cases = [c for c in data['cases'] if c['source'] == 'developer']
```

### Filter by Tag
```python
cases = [c for c in data['cases'] if 'banking' in c['tags']]
```

### Negative Tests Only
```python
cases = [c for c in data['cases'] if c['expectedDetection'] == False]
```

---

## 🛠️ Scripts Available

### generate_test_cases.py
**Purpose:** Generate or regenerate test cases
```bash
python generate_test_cases.py
```

### run_tests.py (Example)
**Purpose:** Execute tests and report results
See **RUN_TESTS.md** for examples

---

## 📚 Documentation Files

1. **TEST_DATA_README.md** - Full documentation
   - Overview
   - Coverage details
   - Schema explanation
   - Usage examples
   - Performance metrics

2. **RUN_TESTS.md** - Testing guide
   - Quick commands
   - Code examples
   - Common scenarios
   - CI/CD integration

3. **TEST_DATA_SUMMARY.txt** - Quick reference
   - Distribution table
   - Detector coverage
   - Security categories
   - Recommendations

4. **TEST_DATA_INDEX.md** - This file
   - Quick links
   - Overview
   - Category breakdown
   - Search filters

---

## ✅ Quality Assurance

✅ 1,250 test cases
✅ All detectors covered (15 types)
✅ All categories represented
✅ All difficulty levels
✅ Realistic scenarios
✅ 200 negative tests
✅ Multiple formats
✅ Compliance data
✅ Banking data
✅ Performance optimized

---

## 🚀 Next Steps

1. **Download:** test-data/prompts.json
2. **Read:** TEST_DATA_README.md
3. **Execute:** Run examples from RUN_TESTS.md
4. **Analyze:** Review test results
5. **Integrate:** Add to CI/CD pipeline
6. **Monitor:** Track accuracy over time

---

## 📞 Quick Reference

| Need | Resource |
|------|----------|
| Full details | TEST_DATA_README.md |
| Quick start | RUN_TESTS.md |
| Reference | TEST_DATA_SUMMARY.txt |
| Tests | test-data/prompts.json |
| Generator | generate_test_cases.py |

---

**Generated**: 2024-07-25
**Total Cases**: 1,250
**File Size**: 0.49 MB
**Status**: ✅ Production Ready

