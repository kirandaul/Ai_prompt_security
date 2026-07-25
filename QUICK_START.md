# 🚀 Quick Start — Testing Dashboard

## 30-Second Setup

```bash
# Terminal 1: Start Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 3000 --reload

# Terminal 2: Open Browser
http://127.0.0.1:3000/tester
```

That's it! You now have a fully functional detector testing dashboard.

---

## What You'll See

### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│ 🧪 Detector Testing Dashboard                               │
│ [▶ Run Test] [⚡ Run All] [📥 Export] [🗑 Clear]            │
├─────────────────────────┬─────────────────────────────────┤
│                         │                                   │
│  Test Prompts (140+)    │  Prompt Details                  │
│  ─────────────────      │  ─────────────────               │
│  ☐ #1 OpenAI Key       │  Category: SECRET                │
│  ☒ #2 AWS Secret       │  Expected: AWS_SECRET_DETECTOR   │
│  ☐ #3 Slack Webhook    │  Severity: 95                    │
│  ...                    │  Prompt: [...]                  │
│                         │                                  │
│                         │  Test Results                    │
│                         │  ─────────────────               │
│                         │  Status: ✅ PASS                 │
│                         │  Duration: 45ms                  │
│                         │                                  │
│                         │  Findings:                       │
│                         │  🔴 AWS Secret - 95% confidence  │
│                         │                                  │
└─────────────────────────┴─────────────────────────────────┘
```

---

## Common Tasks

### Run a Single Test
1. Click any prompt in the list
2. Click [▶ Run Test]
3. See results appear on the right
4. ✅ PASS or ❌ FAIL shows if expected detector triggered

### Run All Tests
1. Click [⚡ Run All Tests]
2. Confirm dialog
3. Watch progress bar fill (may take 30-60 seconds)
4. See final statistics:
   - Total: 140
   - Passed: 138
   - Failed: 2
   - Pass Rate: 98.6%

### Find Specific Prompts
1. Type in search box: "password", "credit card", "SQL", etc.
2. Or select category: SECRET, PII, ATTACK, ENTERPRISE
3. List updates automatically
4. Click to select

### Save Results
1. Run any test (single or bulk)
2. Click [📥 Export Results]
3. JSON file downloads to your computer
4. Contains: timestamp, totals, and detailed results for each test

---

## Test Categories

| Category | # Tests | Examples |
|----------|---------|----------|
| 🔑 SECRET | 45+ | API keys, AWS secrets, JWT tokens, passwords |
| 👤 PII | 35+ | Credit cards, email, phone, Aadhaar |
| ⚔️ ATTACK | 20+ | SQL injection, XSS, prompt injection |
| 🏢 ENTERPRISE | 25+ | Database creds, OAuth, cloud tokens |
| ✅ SAFE | 15+ | Normal text (should NOT trigger) |

---

## Verify Extension Still Works

```
1. Open https://chatgpt.com
2. Type in prompt: "my password is SecurePass@123"
3. Should see red panel: ❌ BLOCKED
4. Try: "my api key is sk-1234567890abcdefghij"
5. Should block it too ✅
```

---

## View Results

### Single Test Result
```json
{
  "status": "PASS",
  "detectors_found": ["API Key / Secret"],
  "result": {
    "severity": "CRITICAL",
    "action": "BLOCK",
    "findings": [
      {
        "reason": "API Key / Secret",
        "severity": "CRITICAL",
        "confidence": 0.99
      }
    ]
  }
}
```

### Export Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_tests": 140,
  "passed": 138,
  "failed": 2,
  "pass_rate": 0.986,
  "results": [...]
}
```

---

## API Endpoints

### For Testing Dashboard
- `POST /api/tester/scan` — Test single prompt
- `POST /api/tester/bulk-scan` — Test multiple
- `GET /api/tester/detectors` — List detectors

### For Extension (Unchanged)
- `POST /api/scan` — Extension calls this

### For Admin Dashboard (Unchanged)
- `POST /api/login` — Admin login
- `GET /api/admin/overview` — Stats and charts

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Blank dashboard | Check backend is running on 3000 |
| CORS error | Ensure backend is on `http://127.0.0.1:3000` |
| Tests won't run | Check backend logs for errors |
| Extension broken | Reload extension from chrome://extensions |
| Can't export | Run a test first, then export |

---

## File Structure

```
backend/
├── server.py          ← Main API (modified)
├── README.md          ← Documentation (updated)
└── tester/            ← NEW Testing Dashboard
    ├── index.html     ← Dashboard UI
    ├── app.js         ← Testing logic
    └── prompts.js     ← 140+ test cases
```

---

## Key Features

✅ **140+ test cases** — Comprehensive detector coverage
✅ **Single & bulk testing** — Run one or all at once
✅ **PASS/FAIL validation** — Automatic result checking
✅ **Progress tracking** — See bulk test progress in real-time
✅ **Search & filter** — Find tests quickly
✅ **Export results** — JSON download for analysis
✅ **No CORS issues** — Serves from same origin
✅ **Extension compatible** — No changes needed
✅ **Professional UI** — Clean, responsive design
✅ **Fast & lightweight** — Pure HTML/JS/CSS

---

## Next Steps

1. ✅ Open tester: `http://127.0.0.1:3000/tester`
2. ✅ Run a test: Click prompt → [▶ Run Test]
3. ✅ Try bulk: [⚡ Run All Tests]
4. ✅ Export: [📥 Export Results]
5. ✅ Verify extension: Type secret in ChatGPT
6. ✅ Read full docs: `backend/README.md`

---

## Questions?

- **Backend issues?** Check `backend/` logs
- **Dashboard not loading?** Browser F12 → Console tab
- **Extension broken?** Reload from `chrome://extensions`
- **Docs needed?** See `IMPLEMENTATION_COMPLETE.md` or `backend/README.md`

---

**Ready? Open http://127.0.0.1:3000/tester now! 🚀**
