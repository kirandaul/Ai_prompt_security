# ✅ API Key Usage Tracking - CORRECTED IMPLEMENTATION

## What Was Fixed

**Before:** Showed all scans with same-ish timeframe (wrong!)
**After:** Shows ONLY scans that used THIS SPECIFIC KEY (correct!)

---

## How It Works Now

### Scenario: Admin Generates One Key, Distributes to Multiple People

```
Admin generates key: b6d37f2458168a58acfaa9ecf9d18fef0e7e55d14c3da5dd2e8e097920

Admin shares this key with:
├─ User A (uses from laptop)
├─ User B (uses from office-pc)
├─ User C (uses from desktop)
└─ User D (uses from server-01)

All of them use THE SAME KEY to scan multiple times
```

### When Scan Happens

```
User A on laptop:
  ├─ POST /api/scan with X-Activation-Key: b6d37f2458168a58...
  ├─ Backend validates key ✓
  ├─ Backend logs scan to database WITH:
  │  ├─ severity: HIGH
  │  ├─ hostname: "my-laptop"
  │  ├─ activation_key: "b6d37f2458168a58..." ← KEY STORED!
  │  └─ created_at: 2026-08-01T10:30:00+00:00
  └─ Scan stored in database

User B on office-pc:
  ├─ Same key: b6d37f2458168a58...
  ├─ Backend logs scan WITH:
  │  ├─ severity: MEDIUM
  │  ├─ hostname: "office-pc"
  │  ├─ activation_key: "b6d37f2458168a58..." ← SAME KEY!
  │  └─ created_at: 2026-08-01T11:15:00+00:00
  └─ Scan stored
```

### When Admin Clicks "Usage" Button

```
Admin clicks "📊 Usage" for key: b6d37f2458168a58...

Backend query:
  SELECT hostname, COUNT(*) 
  FROM scans 
  WHERE activation_key = 'b6d37f2458168a58...'  ← ⭐ SPECIFIC KEY ONLY!
  GROUP BY hostname

Results:
  my-laptop    → 23 scans
  office-pc    → 15 scans
  desktop      → 8 scans
  server-01    → 5 scans
  Total: 51 scans made by people using THIS KEY
```

### Popup Shows

```
📊 Key Usage
├─ Key: b6d37f...7920
├─ Total Requests: 51
├─ First Used: 2026-08-01 10:30
├─ Last Used: 2026-08-01 16:45
│
└─ Devices Using This Key:
   ├─ my-laptop (23 requests) - Last: 16:45
   ├─ office-pc (15 requests) - Last: 15:20
   ├─ desktop (8 requests) - Last: 14:10
   └─ server-01 (5 requests) - Last: 13:50
```

---

## Technical Changes

### 1. Database Schema Update

**Added new column to scans table:**

```sql
ALTER TABLE scans ADD COLUMN activation_key TEXT;
```

This stores **which key was used** for each scan.

### 2. Log Scan Function

**Updated signature:**

```python
def log_scan(
    ...,
    activation_key: Optional[str] = None  # ← NEW!
) -> None:
    # Now stores activation_key in database
    INSERT INTO scans (..., activation_key)
    VALUES (..., activation_key)
```

### 3. All Scan Endpoints Updated

All endpoints now pass the activation_key:

```python
# /api/scan
storage.log_scan(
    ...
    activation_key=activation_key  # ← Passed from dependency
)

# /api/scan-image  
storage.log_scan(
    ...
    activation_key=activation_key  # ← Passed from dependency
)

# /api/scan-document
storage.log_scan(
    ...
    activation_key=activation_key  # ← Passed from dependency
)
```

### 4. Key Usage Query

**CORRECTED to query by activation_key directly:**

```python
def get_key_usage(key: str) -> dict:
    # Query ONLY scans that used THIS KEY
    rows = conn.execute(
        """
        SELECT hostname, COUNT(*) as count, MAX(created_at) as last_used
        FROM scans
        WHERE activation_key = ?  # ← SPECIFIC KEY ONLY!
        GROUP BY hostname
        ORDER BY count DESC
        """,
        (key,)
    )
```

---

## Example: Admin Wants to Know Who Used a Key

### Setup

Admin generated key: `b6d37f2458168a58...` on 2026-08-01

Admin distributed to 4 people:
```
Person 1 (my-laptop):    Uses key from laptop
Person 2 (office-pc):    Uses key from office PC
Person 3 (desktop):      Uses key from desktop
Person 4 (server-01):    Uses key from server
```

### Usage Over 1 Day

```
8:00-10:00  → my-laptop: 8 scans
10:00-12:00 → office-pc: 6 scans
12:00-14:00 → desktop: 4 scans
14:00-16:00 → my-laptop: 15 more scans (total 23)
15:00-15:30 → office-pc: 9 more scans (total 15)
16:00-16:30 → server-01: 5 scans
```

### Admin Clicks "Usage"

```
Click: "📊 Usage" button on key b6d37f...7920

Dashboard calls: GET /api/admin/key-usage/b6d37f2458168a58...

Backend processes:
  SELECT hostname, COUNT(*), MAX(created_at)
  FROM scans
  WHERE activation_key = 'b6d37f2458168a58...'
  GROUP BY hostname

Result:
  my-laptop    23 scans
  office-pc    15 scans
  desktop      4 scans
  server-01    5 scans

Popup shows this list sorted by most-used first
```

---

## Key Difference: Before vs After

### BEFORE (WRONG)
```
Query: "Show me all scans AFTER this key was created"
Result: Shows ALL scans, not just ones using THIS key
Problem: If 10 keys were created, you see scans from all of them!
```

### AFTER (CORRECT)
```
Query: "Show me scans WHERE activation_key = THIS_KEY"
Result: Shows ONLY scans that used THIS specific key
Benefit: Perfect tracking of who used which key!
```

---

## Real-World Example

### Scenario

```
Friday 3 PM:
  Admin: "Generate key for hackathon"
  System: Creates key ABC
  Action: Gives to 50 hackathon participants

Friday 4 PM - Saturday 6 PM:
  50 people using key ABC scanning prompts
  Database logs each scan with:
    - Which person's hostname
    - activation_key: ABC
    - What they scanned
    - Timestamp

Saturday 10 AM:
  Admin: "Who used the hackathon key?"
  Admin: Clicks "📊 Usage" on key ABC
  System: Shows popup listing all 50 laptops/desktops/phones used
```

### What Admin Sees

```
📊 Usage - Hackathon Key (ABC)
├─ Total: 2,547 scans
├─ Unique Devices: 48 (2 didn't show up)
│
├─ Most Active:
│  ├─ laptop-john (315 scans)
│  ├─ desktop-sarah (289 scans)
│  ├─ laptop-mike (267 scans)
│  └─ ... 45 more ...
│
├─ Least Active:
│  ├─ iphone-alex (3 scans)
│  └─ tablet-emma (0 scans - didn't use)
```

---

## Files Changed

### Backend

1. **storage.py**
   - Added `activation_key` column to scans table
   - Updated `log_scan()` to accept and store activation_key
   - Updated `get_key_usage()` to query by activation_key (FIXED!)

2. **server.py**
   - Updated `/api/scan` to pass activation_key to log_scan
   - Updated `/api/scan-image` to pass activation_key to log_scan
   - Updated `/api/scan-document` to pass activation_key to log_scan

### Frontend

1. **dist/src/App.jsx**
   - "📊 Usage" button (already added)
   - Popup displays correctly (already working)

---

## API Endpoint

### Request

```bash
GET /api/admin/key-usage/{key}

Example:
GET /api/admin/key-usage/b6d37f2458168a58acfaa9ecf9d18fef0e7e55d14c3da5dd2e8e097920
```

### Response

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

---

## How It Solves Your Problem

### Original Question
> "When someone uses an API key, I need to know which key was used for each query and from which hostname"

### Solution
✅ **Each scan is now logged with:**
- The exact activation_key used
- The hostname that made the request
- Timestamp of when

✅ **When you click "Usage":**
- Shows ALL scans that used THAT SPECIFIC KEY
- Groups by hostname
- Shows count per hostname
- Shows last used timestamp

✅ **Result:**
- Perfect audit trail
- Know exactly who used which key
- See all hostnames using each key
- Track usage patterns

---

## Summary

🎯 **Feature:** Track which people/devices used each API key
📊 **Mechanism:** Store activation_key with each scan
🔍 **Usage:** Click "📊 Usage" to see all hostnames using that key
✅ **Fixed:** Now queries by specific key (not just by timeframe)
🔒 **Security:** Admin-only access, key truncated in display

---

**Now correctly tracks which hostnames used which API keys!** 🎉
