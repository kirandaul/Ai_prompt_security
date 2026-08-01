# Backend Startup Guide

## The Document Scanning API

The extension tries to call: `http://localhost:3000/api/scan-document`

This endpoint is defined in `backend/app.py` and needs to be running.

---

## How to Start the Backend

### Option 1: Using app.py with Uvicorn (Recommended)

```bash
# Navigate to backend folder
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start server on port 3000
uvicorn app:app --host 127.0.0.1 --port 3000 --reload
```

**Output should show:**
```
INFO:     Uvicorn running on http://127.0.0.1:3000
INFO:     Application startup complete
```

### Option 2: Using server.py (Alternative)

```bash
cd backend
uvicorn server:app --host 127.0.0.1 --port 3000 --reload
```

### Option 3: Using Python directly

```bash
cd backend

# Create simple startup script
cat > run.py << 'EOF'
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=3000, reload=True)
EOF

# Run it
python run.py
```

---

## Verify the Backend is Running

### Test 1: Check Homepage
```
GET http://localhost:3000/
```

Should return:
```json
{
  "message": "Cybage Browser Prompt Detection Running"
}
```

### Test 2: Check Text Scanning Endpoint
```
POST http://localhost:3000/api/scan

{
  "prompt": "My credit card is 4111111111111111"
}
```

Should return findings.

### Test 3: Check Document Scanning Endpoint
```
POST http://localhost:3000/api/scan-document

{
  "document": "<base64 encoded PDF>",
  "filename": "test.pdf",
  "document_type": "pdf"
}
```

Should return document scan results.

---

## Common Issues

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Check what's using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app:app --port 3001 --reload
# Then update extension: change localhost:3000 to localhost:3001
```

### Dependencies Missing
```
ModuleNotFoundError: No module named 'pypdf'
```

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### CORS Error in Browser Console
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:** Already fixed in app.py with:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Document Scanner Not Working
```
Failed to scan document: API error: 404
```

**Solution:** Make sure backend is running on port 3000

---

## Testing the Full Flow

### 1. Start Backend
```bash
cd backend
uvicorn app:app --host 127.0.0.1 --port 3000 --reload
```

### 2. Load Extension
- Chrome: chrome://extensions
- Enable Developer Mode
- Click "Load unpacked"
- Select extension folder

### 3. Open ChatGPT
- Go to https://chatgpt.com

### 4. Create Test PDF
- Create a simple text file with: `My PAN is BT123456L`
- Save as `test.pdf` (or use any PDF with sensitive data)

### 5. Upload File
- Try to upload the PDF in ChatGPT
- Check browser console (F12)
- Should see: `📄 Document Scanner initialized`
- Should see: `Scanning document: test.pdf`
- Should see: Response from backend

### 6. Expected Result
- ✅ If safe: `✅ No sensitive data found`
- 🔒 If sensitive: `🔒 Document Blocked` popup appears

---

## Production Deployment

### For Production (not localhost):

Update `extension/js/document_scanner.js`:

```javascript
// Change from:
this.apiEndpoint = 'http://localhost:3000/api/scan-document';

// To:
this.apiEndpoint = 'https://your-api-domain.com/api/scan-document';
```

And start backend:
```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --ssl-keyfile=/path/to/key --ssl-certfile=/path/to/cert
```

---

## Debugging

### Enable Logging

Add to `backend/app.py`:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.post("/api/scan-document")
async def scan_document(request: DocumentScanRequest):
    logger.debug(f"Received document: {request.filename}")
    # ... rest of code
```

### Check Browser Console (F12)
```
📄 Document Scanner initialized
Scanning document: report.pdf
📄 Document scan result: {...}
```

### Check Backend Logs
```
INFO:     POST /api/scan-document HTTP/1.1" 200 OK
```

---

## Summary

**To use Document Detection:**

1. ✅ Backend files created (app.py with /api/scan-document)
2. ✅ Dependencies added to requirements.txt
3. ✅ Extension code references correct endpoint

**To make it work:**

1. Run: `cd backend && pip install -r requirements.txt`
2. Run: `uvicorn app:app --port 3000 --reload`
3. Load extension in Chrome
4. Test upload in ChatGPT

**The endpoint exists, just need to start the server!** 🚀
