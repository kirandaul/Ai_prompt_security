# 🔧 Fix: CORS Preflight Error (OPTIONS 400)

## Problem

When the extension calls the backend API with the activation key, you see:

```
Request Method: OPTIONS
Status Code: 400 Bad Request
URL: http://127.0.0.1:3000/api/scan
```

The backend returns error for the preflight request, so the actual POST request never happens.

## Root Cause

**CORS (Cross-Origin Resource Sharing) Preflight:**

1. Extension runs on `chatgpt.com` (or Claude)
2. Extension tries to call `http://127.0.0.1:3000/api/scan`
3. Browser sees **different origin** (different domain/port)
4. Browser sends preflight **OPTIONS** request first to ask: "Is this origin allowed?"
5. Backend didn't include `X-Activation-Key` in allowed headers
6. Browser rejects preflight → 400 ❌
7. Actual POST request **never sent**

**Timeline:**
```
OPTIONS http://127.0.0.1:3000/api/scan
  Request headers:
    - Origin: https://chatgpt.com
    - Access-Control-Request-Headers: Content-Type, X-Activation-Key
  ↓
Backend returns: 400 (didn't allow X-Activation-Key header)
  ↓
Browser cancels real POST request
  ↓
Extension gets error ❌
```

## Solution

### Before (server.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.(openai\.com|claude\.ai)$",
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],  # ← Missing X-Activation-Key!
    max_age=600,
)
```

### After (server.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.(openai\.com|claude\.ai)$",
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-Activation-Key"],  # ← Added!
    max_age=600,
)
```

## What Changed

**CORS Configuration:**

| Setting | Before | After | Why |
|---------|--------|-------|-----|
| `allow_methods` | ["POST", "GET", "OPTIONS"] | [same] | OPTIONS needed for preflight |
| `allow_headers` | ["Content-Type"] | ["Content-Type", "X-Activation-Key"] | Allow custom header |
| `max_age` | 600 | 600 | Browser caches preflight for 10 min |

## How CORS Works Now

```
1. Extension prepares request:
   POST /api/scan
   Headers:
     - Content-Type: application/json
     - X-Activation-Key: 64charkey...
   Body: { prompt: "..." }

2. Browser sees different origin → sends OPTIONS preflight
   OPTIONS /api/scan
   Headers:
     - Origin: https://chatgpt.com
     - Access-Control-Request-Method: POST
     - Access-Control-Request-Headers: Content-Type,X-Activation-Key

3. Backend receives OPTIONS request
   ✅ Checks CORS config
   ✅ Sees "X-Activation-Key" in allow_headers
   ✅ Sees "chatgpt.com" in allowed origins
   ✅ Returns 200 OK with CORS headers

4. Browser sees successful preflight response
   ✅ Proceeds with actual POST request

5. Backend receives POST /api/scan
   ✅ Processes request normally
   ✅ Calls verify_activation_key() dependency
   ✅ Validates X-Activation-Key header
   ✅ Runs detection
   ✅ Returns results
```

## Files Changed

- `backend/server.py` - Added `"X-Activation-Key"` to `allow_headers`

**No other changes needed:**
- ✅ Extension: No change
- ✅ Dashboard: No change
- ✅ Database: No change
- ✅ Detection logic: No change

## How to Apply

### Step 1: Verify File Change
```python
# backend/server.py line ~320-325
allow_headers=["Content-Type", "X-Activation-Key"]  # ← Should have this now
```

### Step 2: Backend Auto-Reload
Since backend runs with `--reload`, it auto-detects file changes:
```bash
python -m uvicorn server:app --host 127.0.0.1 --port 3000 --reload
```

If not auto-reloading, restart:
```bash
# Kill old process
Ctrl+C

# Restart
python -m uvicorn server:app --host 127.0.0.1 --port 3000 --reload
```

### Step 3: Reload Extension in Chrome
```
1. chrome://extensions/
2. Find "Cybage Browser Prompt Detection"
3. Click the reload icon
```

### Step 4: Test
```
1. Go to ChatGPT/Claude
2. Type: "my aws server is not working"
3. ✅ Should be ALLOWED (not blocked)
4. Type: "My AWS key is AKIAIOSFODNN7EXAMPLE"
5. ✅ Should be BLOCKED (red popup)
```

## Verification

### In Browser DevTools

**Network Tab:**
```
OPTIONS /api/scan (200 OK) ← Preflight passes
↓
POST /api/scan (200 OK) ← Actual request succeeds
```

**Headers (OPTIONS response should include):**
```
Access-Control-Allow-Origin: https://chatgpt.com
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-Activation-Key
Access-Control-Max-Age: 600
```

### Console Errors (should NOT see)
```
❌ Access to XMLHttpRequest at 'http://127.0.0.1:3000/api/scan' 
   from origin 'https://chatgpt.com' has been blocked by CORS policy
```

If you see this error, the fix didn't apply. Check:
1. File saved: `backend/server.py` line ~323
2. Backend restarted
3. Browser cache cleared (Ctrl+Shift+Delete)

## Why This Works

**CORS Preflight Flow:**

1. **Browser sends OPTIONS** with header requirements
2. **Backend responds** with which headers are allowed
3. **Browser verifies** response matches request
4. **Browser allows POST** if match successful
5. **Activation key sent** in X-Activation-Key header
6. **Backend validates** key
7. **Detection runs** with authenticated request

## Security Notes

✅ **X-Activation-Key is allowed** - required for authentication
✅ **Origin restricted** - only chatgpt.com, claude.ai, localhost
✅ **Methods restricted** - only POST, GET, OPTIONS
✅ **Credentials required** - X-Activation-Key must be valid
✅ **HTTPS in production** - localhost exception for dev only

## Testing Scenarios

### Scenario 1: Safe Text
```
Input: "my aws server is not working"
Expected: OPTIONS 200 + POST 200
Result: SAFE ✅
```

### Scenario 2: Sensitive Text
```
Input: "My AWS key is AKIAIOSFODNN7EXAMPLE"
Expected: OPTIONS 200 + POST 200
Result: BLOCKED ✅
```

### Scenario 3: No Activation Key
```
Input: Any text
Headers: Missing X-Activation-Key
Expected: OPTIONS 200 + POST 401
Result: Unauthorized ✅
```

### Scenario 4: Invalid Activation Key
```
Input: Any text
Headers: X-Activation-Key: invalid123
Expected: OPTIONS 200 + POST 401
Result: Unauthorized ✅
```

## Troubleshooting

### Still seeing OPTIONS 400?

**Check 1: Verify file change**
```bash
cd backend
grep -n "allow_headers" server.py
# Should show: allow_headers=["Content-Type", "X-Activation-Key"]
```

**Check 2: Backend restarted?**
```bash
# Kill and restart
python -m uvicorn server:app --host 127.0.0.1 --port 3000 --reload
```

**Check 3: Browser cache cleared?**
```
Ctrl+Shift+Delete → Clear cache → Reload page
```

**Check 4: Extensions reloaded?**
```
chrome://extensions/ → Find extension → Click reload
```

### Still getting errors?

Check browser console for exact CORS error:
```
F12 → Console tab → Look for "Access to XMLHttpRequest" error
Copy full error message
```

## Summary

✅ **Fixed:** CORS preflight now succeeds
✅ **Changed:** 1 file (server.py)
✅ **Impact:** Extension can send X-Activation-Key header
✅ **Result:** Backend receives authenticated requests with activation key

**System now fully operational!**

---

**Before fix:** ❌ OPTIONS 400 → POST never sent
**After fix:** ✅ OPTIONS 200 → POST 200 → Detection runs
