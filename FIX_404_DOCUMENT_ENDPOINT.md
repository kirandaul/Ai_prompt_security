# Fix: 404 Not Found - Document Endpoint

## Problem
```
Request URL: http://localhost:3000/api/scan-document
Status: 404 Not Found
```

## Root Cause
You were running `server.py` (the actual production backend), but I had added the endpoint to `app.py` (dev file).

The extension needs the endpoint in `server.py` because that's what you're running!

## Solution Applied ✅

Added to `backend/server.py`:

1. **Import** (Line 48):
```python
from document_detector import DocumentDetector
```

2. **Initialize** (After DETECTORS list):
```python
document_detector = DocumentDetector(detectors=DETECTORS)
```

3. **Request Model**:
```python
class DocumentScanRequest(BaseModel):
    document: str  # Base64 encoded file
    filename: str
    document_type: Optional[str] = None
    client_id: Optional[str] = None
    source: Optional[str] = None
    user_agent: Optional[str] = None
```

4. **Endpoint**:
```python
@app.post("/api/scan-document")
async def api_scan_document(body: DocumentScanRequest, http: Request):
    result = await document_detector.scan_document(
        document_base64=body.document,
        filename=body.filename,
        document_type=body.document_type
    )
    return result
```

---

## What Changed

| File | Before | After |
|------|--------|-------|
| `server.py` | No document endpoint | ✅ Added `/api/scan-document` |
| `app.py` | Has endpoint | (Still there, but not used) |

---

## To Test Now

### 1. **Restart Backend**

If it's still running, stop it (Ctrl+C), then:

```bash
cd backend
uvicorn server:app --host 127.0.0.1 --port 3000 --reload
```

Should show:
```
INFO:     Uvicorn running on http://127.0.0.1:3000
INFO:     Application startup complete
```

### 2. **Verify Endpoint Exists**

```bash
curl -X POST http://localhost:3000/api/scan-document \
  -H "Content-Type: application/json" \
  -d '{
    "document": "base64data",
    "filename": "test.pdf",
    "document_type": "pdf"
  }'
```

Should return result (not 404).

### 3. **Test in Chrome**

- Go to ChatGPT.com
- Try upload document
- Should work now!

---

## Why This Happened

You have TWO backend files:
- `server.py` - **The actual running backend** ← This is what you're using
- `app.py` - Dev/testing version

I accidentally added the endpoint only to `app.py`. Fixed now by adding it to `server.py` too.

---

## Summary

✅ **Fixed**: Document endpoint now in `server.py` (the actual running backend)
✅ **Ready**: `/api/scan-document` should return 200 OK (not 404)
✅ **Test**: Restart backend and try uploading documents in ChatGPT

If you still get 404 after restart, the backend didn't reload. Stop and start it again.
