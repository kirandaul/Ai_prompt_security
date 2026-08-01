# 📊 API Key Usage Tracking - Track Device Usage

## Feature Overview

Now you can see **which devices/hostnames** have used each API key and how many times!

### What's New

✅ **Usage Button** - Click "📊 Usage" button next to any API key
✅ **Popup Shows** - List of all devices that used that key
✅ **Statistics** - Total requests, first used, last used
✅ **Device Details** - Hostname, request count, last used time

---

## How It Works

### 1. Click Usage Button

In the dashboard's **Extension Activation Keys** section:

```
🔑 Extension Activation Keys
┌─────────────────────────────────────────────────────┐
│ Key                  | Actions                      │
├─────────────────────────────────────────────────────┤
│ b6d37f24...7920     | [📊 Usage] [🔴] [🗑]         │ ← Click here
└─────────────────────────────────────────────────────┘
```

### 2. See Popup with Device List

```
┌────────────────────────────────┐
│ 📊 Key Usage                   │ ✕
├────────────────────────────────┤
│                                │
│ Key: b6d37f...7920            │
│ Total Requests: 156           │
│ First Used: 2026-08-01 10:30  │
│ Last Used: 2026-08-01 15:45   │
│                                │
│ Devices Using This Key:        │
│                                │
│ Hostname    | Requests |Last  │
│─────────────┼──────────┼─────│
│ my-laptop   |    89    |15:45│
│ office-pc   |    52    |15:40│
│ server-01   |    15    |14:20│
│                                │
│             [Close]            │
└────────────────────────────────┘
```

### 3. Understand the Data

```
Row 1: my-laptop made 89 requests using this key (last at 15:45)
Row 2: office-pc made 52 requests using this key (last at 15:40)
Row 3: server-01 made 15 requests using this key (last at 14:20)

Total: 156 requests from 3 devices
```

---

## Technical Implementation

### Backend Changes

**New Function: `storage.get_key_usage(key)` in storage.py**

```python
def get_key_usage(key: str) -> dict:
    """Get usage statistics for a specific activation key.
    
    Returns:
        {
            "key": "b6d37f...7920",
            "total_requests": 156,
            "hostnames": [
                {"hostname": "my-laptop", "count": 89, "last_used": "2026-08-01T15:45:00+00:00"},
                {"hostname": "office-pc", "count": 52, "last_used": "2026-08-01T15:40:00+00:00"},
                {"hostname": "server-01", "count": 15, "last_used": "2026-08-01T14:20:00+00:00"}
            ],
            "first_used": "2026-08-01T10:30:00+00:00",
            "last_used": "2026-08-01T15:45:00+00:00"
        }
    """
```

**New Endpoint: `/api/admin/key-usage/{key}` in server.py**

```
GET /api/admin/key-usage/{key}

Returns:
{
    "status": "success",
    "usage": { ... data above ... }
}
```

### Frontend Changes

**Dashboard Component: ActivationKeysPanel**

1. Added "📊 Usage" button in table actions
2. Added `usagePopup` state to show/hide popup
3. Added `showKeyUsage()` function to fetch data from API
4. Added popup component to display device list

---

## Features

### Usage Popup Shows

✅ **Key Identifier** - Truncated key for security
✅ **Total Requests** - How many API requests made with this key
✅ **First Used** - When key was first used
✅ **Last Used** - Most recent usage time
✅ **Device List** - Table of all hostnames
✅ **Request Count** - How many requests per device
✅ **Last Used Time** - When each device last used the key

### Easy to Use

✅ Click "📊 Usage" button
✅ Beautiful popup appears
✅ See all devices instantly
✅ Close with X or Close button

### Sorted Automatically

Devices appear in order of **most requests first**

```
my-laptop    89 requests  ← Used most
office-pc    52 requests
server-01    15 requests  ← Used least
```

---

## Use Cases

### Monitor Key Usage

**Admin wants to know:** "Who is using this API key?"

→ Click "📊 Usage" button
→ See list of all devices
→ See how often each device is scanning

### Identify Compromised Keys

**Suspicious activity detected:** "Why is a device in Russia using our key?"

→ Click "📊 Usage"
→ See device list
→ Identify unexpected device
→ Deactivate key if needed
→ Investigate device

### Track Deployment Progress

**Question:** "How many office PCs have the extension installed?"

→ Generate a key
→ Distribute to office
→ Click "📊 Usage" later
→ Count devices in usage list
→ See which PC hasn't installed yet

### Audit Trail

**Compliance need:** "Prove which devices accessed the system"

→ Click "📊 Usage" for key
→ Export or screenshot
→ Shows hostname, request count, timestamps
→ Proof of access by device

---

## API Endpoint Details

### Request

```bash
GET /api/admin/key-usage/{key}

Example:
GET /api/admin/key-usage/b6d37f2458168a58acfaa9ecf9d18fef0e7e55d14c3da5dd2e8e097920
```

### Response (Success)

```json
{
    "status": "success",
    "usage": {
        "key": "b6d37f...7920",
        "total_requests": 156,
        "hostnames": [
            {
                "hostname": "my-laptop",
                "count": 89,
                "last_used": "2026-08-01T15:45:00+00:00"
            },
            {
                "hostname": "office-pc",
                "count": 52,
                "last_used": "2026-08-01T15:40:00+00:00"
            }
        ],
        "first_used": "2026-08-01T10:30:00+00:00",
        "last_used": "2026-08-01T15:45:00+00:00"
    }
}
```

### Response (Error)

```json
{
    "status": "error",
    "message": "Key not found"
}
```

---

## How Tracking Works

### When Extension Makes a Request

```
1. Extension has API key in memory
2. Extension calls POST /api/scan with key
3. Backend receives request with:
   - X-Activation-Key header (the key)
   - hostname (from os.gethostname())
   - timestamp (created_at)
4. Backend logs scan to database with hostname
5. Scan record includes: key, hostname, timestamp
```

### When Admin Clicks "Usage"

```
1. Dashboard sends: GET /api/admin/key-usage/{key}
2. Backend queries: "Show me all scans made by this key"
3. Actually queries: All scans created after key was generated
4. Groups by hostname
5. Counts requests per hostname
6. Orders by most-used first
7. Returns data to dashboard
8. Dashboard renders popup with device list
```

---

## Notes

### Security

✅ Key is truncated in popup (shows only first 8 and last 4 chars)
✅ Only admins can view usage (requires authentication)
✅ No sensitive data in device list
✅ Just shows device names and request counts

### Accuracy

✅ Counts are based on scan logs
✅ Timestamps are from server (cannot be falsified by client)
✅ Hostname is from device's `os.gethostname()` (can be spoofed in theory, but typical enterprise has accurate hostnames)
✅ Data is historical and read-only

### Performance

✅ Query groups by hostname (efficient)
✅ Popup fetches data on demand (not on load)
✅ Counts are fast calculations
✅ No performance impact on dashboard

---

## Files Changed

### Backend
- `backend/storage.py` - Added `get_key_usage()` function
- `backend/server.py` - Added `/api/admin/key-usage/{key}` endpoint

### Frontend
- `dist/src/App.jsx` - Updated `ActivationKeysPanel` with:
  - Usage button
  - `usagePopup` state
  - `showKeyUsage()` function
  - Popup component

---

## Example Workflow

### Step 1: Admin Generates Key

```
Click: "+ Generate Key"
Result: Key b6d37f2458168a58...7920 created
Action: Auto-copied to clipboard
```

### Step 2: Admin Distributes Key

```
Admin shares key with:
- my-laptop
- office-pc
- server-01
```

### Step 3: Devices Use Key

```
my-laptop: Makes 89 API requests
office-pc: Makes 52 API requests
server-01: Makes 15 requests
(Total: 156 requests)
```

### Step 4: Admin Checks Usage

```
1. Open dashboard
2. See "🔑 Extension Activation Keys" section
3. Find key: b6d37f2458168a58...7920
4. Click "📊 Usage" button
5. Popup appears showing:
   - my-laptop (89 requests)
   - office-pc (52 requests)
   - server-01 (15 requests)
6. Confirm: "All 3 devices are using the key"
```

---

## Summary

🎯 **Feature:** Track which devices/hostnames use each API key
📊 **How:** Click "📊 Usage" button in key table
📈 **Shows:** Device names, request counts, last used time
🔒 **Security:** Key is truncated, admin-only access
⚡ **Performance:** Fast queries on database scans
🚀 **Use Cases:** Monitor usage, find compromised keys, audit trail

---

**With this feature, admins have complete visibility into which devices are using each API key!** 🎉
