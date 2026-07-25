# Backend — Detection Engine & API

FastAPI service: 15 detectors, SQLite audit log, admin auth, and image OCR.
The extension calls it; the dashboard reads from it.

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

## Optional
```bash
python seed_demo.py --reset     # fill the dashboard with demo data
python -m unittest tests.test_server -v   # run the detector tests
python benchmark.py             # 1000-case accuracy benchmark (TP/FP/TN/FN)
python benchmark.py 250         # smaller run
```

The benchmark stores its results in the same SQLite file and they appear in the
**Detection Accuracy** panel on the dashboard, including every case we got wrong.

## Endpoints
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/scan` | none | scan a text prompt (extension) |
| POST | `/api/scan-image` | none | OCR + scan an image (extension) |
| POST | `/api/login` `/api/logout` | — | admin session |
| GET | `/api/admin/overview` | cookie | dashboard KPIs + charts |
| GET | `/api/admin/logs` | cookie | filtered, newest-first events |

## Admin credentials (change for real use)
Set env vars before starting:
```
PSG_ADMIN_USER=admin
PSG_ADMIN_PASSWORD=admin123
PSG_SECRET_KEY=<random-long-string>   # keeps sessions valid across restarts
```

## Notes
- **Database:** SQLite file `psg_logs.db` (auto-created). No server needed.
- **Privacy:** stored prompts are **redacted** — real secrets are never saved.
- **Image OCR** is optional; if the OCR packages are absent, `/api/scan-image`
  returns gracefully and text scanning still works.
- **Detectors** live in `detectors/` — one small class each; add/edit freely.
