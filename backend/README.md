# Backend — Cybage Browser Prompt Detection Engine

FastAPI service: 15+ detectors, SQLite audit log, admin auth, image OCR, and **integrated testing dashboard**.
The extension calls it; the dashboard reads from it; the tester validates it.

## Requirements
- **Python 3.12+**
- Packages in `requirements.txt` (FastAPI, Uvicorn, Pydantic, and — for image
  scanning — rapidocr-onnxruntime, Pillow, numpy).

## Install
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn server:app --host 127.0.0.1 --port 3000
# add --reload during development
```
Health check: `curl http://127.0.0.1:3000/health` → `{"status":"ok","detectors":15}`

## Quick Start — Testing Dashboard

Open the **integrated testing dashboard** to validate detectors against 140+ test cases:

```bash
# 1. Start the backend
uvicorn server:app --host 127.0.0.1 --port 3000 --reload

# 2. Open browser
http://127.0.0.1:3000/tester
```

### Dashboard Features
- **Prompt List** — Browse 140+ test cases organized by category (SECRET, PII, ATTACK, ENTERPRISE)
- **Single Test** — Run one prompt, view full API response with findings
- **Bulk Test** — Run all prompts sequentially (100ms delay between requests), track progress
- **Search & Filter** — Find prompts by name, text, or category
- **Result Validation** — PASS/FAIL badge shows if expected detector was triggered
- **Export Results** — Download test results as JSON with timestamp, totals, and detailed outcomes

### Tester Architecture
The tester makes **same-origin** API calls to the backend:
- **CORS-enabled origins:** `http://127.0.0.1:3000`, `http://localhost:3000`, `http://localhost:5500`
- **API endpoints:**
  - `POST /api/tester/scan` — Scan a single test prompt with metadata (expected_detector, category, severity)
  - `POST /api/tester/bulk-scan` — Scan multiple prompts sequentially
  - `GET /api/tester/detectors` — List available detectors for reference

No extension modification required — the tester uses the **same `/api/scan` contract** as the Chrome extension.

## Extension Compatibility

The Chrome extension continues to work unchanged:
- **Endpoint:** `https://chatgpt.com` or `https://claude.ai` → `POST http://127.0.0.1:3000/api/scan`
- **Origin:** Chrome extension origin is allowed via `allow_origin_regex`
- **Request/Response:** Identical contract (prompt → findings + action)

The tester dashboard runs on the **same server** (localhost:3000), avoiding CORS issues entirely.

## Optional
```bash
python seed_demo.py --reset     # fill the dashboard with demo data
python -m unittest tests.test_server -v   # run the detector tests
python benchmark.py             # 1000-case accuracy benchmark (TP/FP/TN/FN)
python benchmark.py 250         # smaller run
```

The benchmark stores its results in the same SQLite file and they appear in the
**Detection Accuracy** panel on the dashboard, including every case we got wrong.

## API Endpoints

### Production (Extension & Dashboard)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/scan` | none | scan a text prompt (extension) |
| POST | `/api/scan-image` | none | OCR + scan an image (extension) |
| POST | `/api/login` `/api/logout` | — | admin session |
| GET | `/api/admin/overview` | cookie | dashboard KPIs + charts |
| GET | `/api/admin/logs` | cookie | filtered, newest-first events |

### Testing Dashboard (New)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/tester/scan` | scan a single test prompt with expected_detector |
| POST | `/api/tester/bulk-scan` | scan multiple test prompts sequentially |
| GET | `/api/tester/detectors` | list available detectors + labels |
| GET | `/tester` | serve the testing dashboard (HTML/JS/CSS) |

## Admin credentials (change for real use)
Set env vars before starting:
```
PSG_ADMIN_USER=admin
PSG_ADMIN_PASSWORD=admin123
PSG_SECRET_KEY=<random-long-string>   # keeps sessions valid across restarts
```

## CORS Configuration

**Allowed Origins** (see `server.py`):
```python
ALLOWED_ORIGINS = [
    "https://chatgpt.com",
    "https://chat.openai.com",
    "https://claude.ai",
    "http://localhost:3000",      # tester dashboard
    "http://127.0.0.1:3000",      # tester dashboard
    "http://localhost:5500",       # local dev server
    "http://127.0.0.1:5500",       # local dev server
]
```

Extension origins are matched via regex: `r"https://.*\.(openai\.com|claude\.ai)$"`

## Notes
- **Database:** SQLite file `psg_logs.db` (auto-created). No server needed.
- **Privacy:** stored prompts are **redacted** — real secrets are never saved.
- **Image OCR** is optional; if the OCR packages are absent, `/api/scan-image`
  returns gracefully and text scanning still works.
- **Detectors** live in `detectors/` — one small class each; add/edit freely.
- **Static Files:** Tester dashboard is mounted at `/tester` using FastAPI's `StaticFiles`.
  Files are in the `tester/` directory (index.html, app.js, prompts.js).

## Test Prompts Structure

Each test prompt in `tester/prompts.js` has:
```javascript
{
  id: 1,                              // unique ID
  name: "OpenAI API Key",             // descriptive name
  category: "SECRET",                 // SECRET | PII | ATTACK | ENTERPRISE | SAFE
  expected_detector: "API_KEY_DETECTOR",  // detector that should trigger
  severity: 100,                      // 0-100 severity expectation
  prompt: "sk-proj-abc..."            // test text
}
```

## Development Workflow

1. **Add new detectors** → `detectors/` folder
2. **Test them** → Open tester dashboard, search/filter test cases, run tests
3. **Review results** → PASS/FAIL badges show coverage
4. **Bulk export** → Download results.json for CI/CD integration
5. **Iterate** → Add more test cases to `tester/prompts.js` as needed

## Troubleshooting

**CORS Error in tester?**
- Ensure backend is running on `http://127.0.0.1:3000`
- Check browser console for blocked requests
- Verify `localhost:5500` is in `ALLOWED_ORIGINS` if testing from elsewhere

**Tester page blank?**
- Check that `tester/` folder exists with `index.html`, `app.js`, `prompts.js`
- Verify no JavaScript errors in browser console
- Ensure `prompts.js` exports `window.PROMPTS` array

**Tests not running?**
- Check backend logs for errors in `/api/tester/scan` endpoint
- Verify detector names match those in `REASON_LABELS` in `server.py`
- Ensure test prompt is within `MAX_PROMPT_LENGTH` (20000 chars)


