# ✅ API Key Usage Tracking - IMPLEMENTATION COMPLETE

## Summary

**Feature Implemented:** Track which specific API keys are used for each scan and show which hostnames/devices used them.

**Status:** ✅ **FULLY WORKING**

Backend: Running at http://localhost:3000  
Endpoint: `/api/admin/key-usage/{key}` ✓ (200 OK responses confirmed)  
Dashboard: http://localhost:5173 - "📊 Usage" button active ✓  
Database: Tracks activation_key with each scan ✓

---

## What Now Works

### 1. **Key Generation → Share → Track Usage**

**Scenario:**
```
Admin generates 1 key
Admin shares with 4 people/devices
All use the same key to scan
Admin clicks "Usage" to see which devices used it
```

**Flow:**
```
User A (my-laptop):
  POST /api/scan with X-Activation-Key: b6d37f24...
  ↓ Stored in database with activation_key column
  ├─ User B (office-pc):
  │   POST /api/scan with X-Activation-Key: b6d37f24...
  │   ↓ Stored with same activation_key
  │
  └─ User C (desktop):
      POST /api/scan with X-Activation-Key: b6d37f24...
      ↓ Stored with same activation_key

Admin clicks "📊 Usage" on key:
  ↓ Popup shows all 3 hostnames that used it
  ├─ my-laptop: 23 scans
  ├─ office-pc: 15 scans
  └─ desktop: 8 scans
```

---

## Technical Implementation

### Files Changed

#### 1. **backend/storage.py**

✅ **Added activation_key column to scans table**
```python
CREATE TABLE IF NOT EXISTS scans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
    activation_key  TEXT  # ← NEW!
)
```

✅ **Updated log_scan() function**
```python
def log_scan(
    ...,
    activation_key: Optional[str] = None  # ← NEW PARAMETER!
) -> None:
    # Now stores which key was used
    INSERT INTO scans (..., activation_key)
    VALUES (..., activation_key)
```

✅ **Fixed get_key_usage() function**
```python
def get_key_usage(key: str) -> dict:
    # CORRECTED: Query by specific key
    SELECT hostname, COUNT(*), MAX(created_at)
    FROM scans
    WHERE activation_key = ?  # ← SPECIFIC KEY ONLY!
    GROUP BY hostname
```

#### 2. **backend/server.py**

✅ **Added /api/admin/key-usage/{key} endpoint**
```python
@app.get("/api/admin/key-usage/{key}")
async def admin_key_usage(key: str, user: str = Depends(require_admin)):
    """Get usage statistics for a specific activation key."""
    usage = storage.get_key_usage(key)
    return {"status": "success", "usage": usage}
```

✅ **Updated all 3 scan endpoints to pass activation_key**

1. **/api/scan** (text scanning)
```python
storage.log_scan(
    ...
    activation_key=activation_key  # ← PASSED!
)
```

2. **/api/scan-image** (image scanning)
```python
storage.log_scan(
    ...
    activation_key=activation_key  # ← PASSED!
)
```

3. **/api/scan-document** (document scanning)
```python
storage.log_scan(
    ...
    activation_key=activation_key  # ← PASSED!
)
```

#### 3. **dist/src/App.jsx** (Already Complete)

✅ **"📊 Usage" button in ActivationKeysPanel**
```jsx
<button 
  onClick={() => showKeyUsage(k.key)}
  title="View which devices used this key"
>
  📊 Usage
</button>
```

✅ **Usage popup modal**
```jsx
{usagePopup && (
  <div>
    <h3>📊 Key Usage</h3>
    <div>Key: {usagePopup.key}</div>
    <div>Total Requests: {usagePopup.total_requests}</div>
    
    {/* List all hostnames that used this key */}
    {usagePopup.hostnames.map(h => (
      <tr>
        <td>{h.hostname}</td>
        <td>{h.count} requests</td>
        <td>{h.last_used}</td>
      </tr>
    ))}
  </div>
)}
```

---

## API Endpoint Reference

### Request

```http
GET /api/admin/key-usage/b6d37f2458168a58acfaa9ecf9d18fef0e7e55d14c3da5dd2e8e097920

Headers:
  Cookie: psg_session=<admin-token>
```

### Response (Success)

```json
{
  "status": "success",
  "usage": {
    "key": "b6d37f...7920",
    "total_requests": 51,
    "hostnames": [
      {
        "hostname": "my-laptop",
        "count": 23,
        "last_used": "2026-08-01T16:45:00+00:00"
      },
      {
        "hostname": "office-pc",
        "count": 15,
        "last_used": "2026-08-01T15:20:00+00:00"
      },
      {
        "hostname": "desktop",
        "count": 8,
        "last_used": "2026-08-01T14:10:00+00:00"
      },
      {
        "hostname": "server-01",
        "count": 5,
        "last_used": "2026-08-01T13:50:00+00:00"
      }
    ],
    "first_used": "2026-08-01T10:30:00+00:00",
    "last_used": "2026-08-01T16:45:00+00:00"
  }
}
```

### Response (Key Not Found)

```json
{
  "status": "error",
  "message": "Key not found"
}
```

---

## How to Use

### 1. Generate a Key

```
Dashboard → "🔑 Extension Activation Keys" panel
Click: "+ Generate Key"
Copy the key (auto-copied to clipboard)
Share key with users
```

### 2. Users Use the Key

**On Extension:**
```
Extension loads
Key prompt appears
User enters the 64-char hex key
Extension stores (encrypted) and uses it
All scans sent with X-Activation-Key header
```

**Backend Logs Each Scan:**
```
POST /api/scan with X-Activation-Key: b6d37f24...
Backend verifies key is active
Backend stores scan with activation_key column populated
```

### 3. Admin Tracks Usage

```
Dashboard → "🔑 Extension Activation Keys" panel
Find the key you shared
Click: "📊 Usage" button
Popup shows all hostnames that used this key
See how many times each used it
See when it was last used
```

---

## Verification Checklist

✅ **Database**
- `scans` table has `activation_key` column
- Auto-migration adds column if missing

✅ **Backend**
- `/api/admin/key-usage/{key}` endpoint exists
- Returns 200 OK (confirmed in logs)
- Backend auto-reloaded with changes

✅ **All Scan Endpoints**
- `/api/scan` passes activation_key ✓
- `/api/scan-image` passes activation_key ✓
- `/api/scan-document` passes activation_key ✓

✅ **Query Logic**
- `get_key_usage()` filters by specific key ✓
- Returns all hostnames that used THAT KEY ✓
- Groups by hostname with count ✓

✅ **Frontend**
- Dashboard button visible ✓
- Popup UI complete ✓
- Fetches from correct endpoint ✓

✅ **Backend Running**
- Process: python -m uvicorn server:app (running)
- Port: 127.0.0.1:3000
- Auto-reload: Active

---

## Real-World Examples

### Example 1: Security Team Distributes Key

```
Scenario: Security team creates a "Production Monitoring" key

Action:
  1. Generate key: k1_prod_monitoring
  2. Share with 3 monitors:
     - monitor-1.prod
     - monitor-2.prod
     - monitor-3.prod

Day 1:
  monitor-1: 450 scans
  monitor-2: 425 scans
  monitor-3: 400 scans
  Total: 1,275 scans

Admin checks usage:
  Click "📊 Usage" on k1_prod_monitoring
  See exactly which monitors used it
  See usage distribution
  Confirm all 3 are active
```

### Example 2: Find Leaked Key

```
Scenario: Security incident - key might be leaked

Known: Key was shared with only 2 people
Unexpected: 5 different hostnames used it

Admin actions:
  1. Click "📊 Usage" on the key
  2. See: 5 hostnames instead of 2
  3. Identify: laptop-unknown (suspicious!)
  4. Click "🔴 Deactivate" immediately
  5. Audit what laptop-unknown scanned
```

### Example 3: Usage Report

```
Scenario: Generate monthly report

Process:
  1. List all keys in dashboard
  2. For each key, click "📊 Usage"
  3. Record: total_requests, hostnames, last_used
  4. Create report:

Key Status Report - August 2026
─────────────────────────────────
k1_production:
  Status: Active
  Shared with: 1 person
  Hostnames: workstation-prod (1,247 scans)
  Last Used: 2026-08-31 23:45

k2_testing:
  Status: Active
  Shared with: 5 people
  Hostnames: 
    - test-lab-1 (567 scans)
    - test-lab-2 (534 scans)
    - test-lab-3 (512 scans)
    - test-lab-4 (489 scans)
    - test-lab-5 (421 scans)
  Last Used: 2026-08-31 22:15

k3_archived:
  Status: Inactive
  Last Used: 2026-08-15 14:30
  No new usage since deactivation
```

---

## How It Prevents Problems

### Problem 1: "Which key was used for this scan?"
**Solution:** activation_key stored in database with each scan ✓

### Problem 2: "Who used this specific key?"
**Solution:** Query database for all hostnames using that key ✓

### Problem 3: "Did someone share the key?"
**Solution:** If more hostnames appear than expected, key was shared ✓

### Problem 4: "When was the key last used?"
**Solution:** last_used timestamp shows activity ✓

### Problem 5: "How much was the key used?"
**Solution:** count shows total scans per hostname ✓

---

## Next Steps (Optional)

If you want to add more features:

1. **Export Usage Report** - Add button to download CSV
2. **Email Alerts** - Notify admin if key used from new hostname
3. **Rate Limiting** - Limit scans per key per time period
4. **Key Expiration** - Auto-deactivate keys after X days
5. **Usage Trends** - Graph showing usage over time
6. **Anomaly Detection** - Alert if usage pattern changes

---

## Troubleshooting

### "Usage popup shows no data"
✓ Check if scans were actually logged with that key
✓ Verify key is active
✓ Check browser console for errors

### "All keys show same usage"
✓ Verify activation_key column exists in database
✓ Check that all endpoints pass activation_key parameter
✓ Backend may need restart (should auto-reload)

### "400 error on key-usage endpoint"
✓ Check key is valid and exists in activation_keys table
✓ Verify admin is authenticated
✓ Check browser console for full error message

### "No scans logged with key"
✓ Verify extension is sending X-Activation-Key header
✓ Check backend receives the header (look in logs)
✓ Verify database column exists: `PRAGMA table_info(scans)`

---

## Summary

🎯 **Feature:** Track which devices used each API key
✅ **Status:** Fully implemented and working
📊 **Mechanism:** Store activation_key with each scan
🔍 **Usage:** Click "📊 Usage" to see all hostnames
🔒 **Security:** Admin-only access, truncated display
✨ **Benefit:** Complete audit trail of API key usage

**Backend endpoint is LIVE and responding with 200 OK!** 🎉

---

**Questions?** Check the logs in the console or refer back to this document.
