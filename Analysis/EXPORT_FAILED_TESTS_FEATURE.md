# Export Failed Test Cases Feature

## Overview
A new feature has been added to the testing dashboard to export all failed test cases to a formatted text file for later analysis and debugging.

## How to Use

### 1. Run Tests
- Open the dashboard: `http://127.0.0.1:3000/tester`
- Click **[⚡ Run All Tests]** to run all 1,250+ test cases
- Wait for tests to complete

### 2. Export Failed Tests
After tests complete, click the new **[📋 Export Failed Tests]** button to download a text file containing:
- All test cases that failed
- Expected detector vs detectors found
- The actual prompt text that failed
- Findings detected by the backend
- Severity and other metadata

### 3. File Format
The exported file `failed-test-cases-TIMESTAMP.txt` contains:
```
FAILED TEST CASES REPORT
========================

Generated: 2024-01-15T10:30:45.123Z
Total Failed: 42

================================================================================
TEST 1: #123 - PostgreSQL Connection with Special Chars
================================================================================

Category: SECRET
Expected Detector: API_KEY_DETECTOR
Detectors Found: TIER2_SECRETS
Severity: CRITICAL
Findings Count: 1
Duration: 45.32ms

PROMPT:
-------
postgresql://admin:SecurePass@db.internal:5432/production

FINDINGS:
---------
1. Basic Auth Credentials (CRITICAL)
   Category: SECRET
   Confidence: 0.9
   Evidence: SecurePass
```

## Buttons in Dashboard

| Button | Function |
|--------|----------|
| ▶ Run Test | Run a single selected test |
| ⚡ Run All Tests | Run all filtered test cases (bulk) |
| 📥 Export Results | Export ALL test results as JSON |
| **📋 Export Failed Tests** | **NEW: Export only FAILED tests as TXT** |
| 🗑 Clear Results | Clear all test results |

## Use Cases

1. **Debugging**: Identify which test cases are failing and why
2. **Analysis**: Review false positives and false negatives
3. **Improvement**: Use failed cases to improve detectors
4. **Reporting**: Generate reports of detector coverage gaps

## File Locations

- Dashboard: `http://127.0.0.1:3000/tester`
- Export button functionality: `backend/tester/app.js` → `exportFailedTests()` function
- HTML button: `backend/tester/index.html`

## Next Steps

1. Run all tests in the dashboard
2. Click **[📋 Export Failed Tests]** to download the report
3. Review the text file to understand which detectors need improvement
4. File will be saved as `failed-test-cases-TIMESTAMP.txt` in your Downloads folder

---

**Note:** The export happens entirely in the browser - no data is sent to the server. The file is generated and downloaded directly.
