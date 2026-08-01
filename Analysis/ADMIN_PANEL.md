# 🎛️ Admin Panel - Activation Key Management

## Overview
The admin panel in the dashboard allows administrators to manage extension activation keys with full control over key lifecycle.

## Dashboard Location
**Path**: http://localhost:3000 → Login → Dashboard

**Section**: "🔑 Extension Activation Keys" panel (below Accuracy section)

## Features

### 1. 🔑 Generate New Key
- **Input**: Hostname (optional)
- **Output**: 64-character hexadecimal key + Extension ID
- **Storage**: Automatically saved to SQLite `activation_keys` table
- **Usage**: Copy key to extension during first install

**Example Response:**
```json
{
  "status": "success",
  "key": "d1c94ecced8113190ac483573c489cc8...",
  "extension_id": "admin-881b42f7",
  "message": "Activation key generated"
}
```

### 2. 📊 View All Keys
- **Display**: Table showing all activation keys
- **Columns**:
  - Status (🟢 Active / 🔴 Inactive)
  - Key (truncated with ...)
  - Extension ID (user-facing identifier)
  - Hostname (device name if provided)
  - Created (timestamp)
  - Last Used (when key was last validated)
  - User Agent (browser/platform info)
- **Sorting**: Newest first (created_at DESC)
- **Pagination**: Latest 100 keys by default

### 3. 🔴 Deactivate Key
- **Action**: Toggle key to inactive state
- **Effect**: Key is no longer valid for API requests
- **Response**: 401 Unauthorized if key is used
- **Reversible**: Can be reactivated later
- **Use Cases**: 
  - Suspicious activity detected
  - Testing access control
  - Temporary suspension

### 4. 🟢 Reactivate Key
- **Action**: Toggle key back to active state
- **Effect**: Key becomes usable again
- **Response**: Requests with key now succeed (200 OK)
- **Time**: Instant re-activation
- **Use Cases**:
  - Resolved false positive
  - Temporary ban lifted
  - Testing re-enablement

### 5. 🗑️ Delete Key
- **Action**: Permanently remove key from database
- **Effect**: Key cannot be reactivated
- **Confirmation**: "Are you sure?" dialog
- **Use Cases**:
  - Compromised key
  - Permanent revocation
  - Cleanup of old/unused keys

### 6. 📈 Statistics
- **Total Keys**: Count of all keys in system
- **🟢 Active**: Count of enabled keys
- **🔴 Inactive**: Count of disabled keys
- **Real-time**: Updates after each action

## Backend Endpoints

### Generate Key
```bash
POST /api/admin/generate-key
Body: { "hostname": "hackathon-066" }
Response: { "status": "success", "key": "...", "extension_id": "..." }
```

### List All Keys
```bash
GET /api/admin/activation-keys?limit=100
Response: { "status": "success", "total": 3, "keys": [...] }
```

### Deactivate Key
```bash
POST /api/admin/deactivate-key?key=d1c94ecced8113190ac483573c489cc8...
Response: { "status": "success", "message": "Key d1c94ec... deactivated" }
```

### Reactivate Key
```bash
POST /api/admin/activate-key?key=d1c94ecced8113190ac483573c489cc8...
Response: { "status": "success", "message": "Key d1c94ec... reactivated" }
```

### Delete Key
```bash
DELETE /api/admin/delete-key?key=d1c94ecced8113190ac483573c489cc8...
Response: { "status": "success", "message": "Key d1c94ec... deleted" }
```

## Database Schema

### activation_keys Table
```sql
CREATE TABLE activation_keys (
    id            INTEGER PRIMARY KEY,
    created_at    TEXT NOT NULL,           -- ISO timestamp
    key           TEXT UNIQUE NOT NULL,    -- 64-char hex key
    extension_id  TEXT NOT NULL,           -- user-facing ID
    hostname      TEXT,                    -- device hostname
    user_agent    TEXT,                    -- browser info
    is_active     INTEGER DEFAULT 1,       -- 1=active, 0=inactive
    last_used     TEXT,                    -- when key was validated
    expires_at    TEXT                     -- expiration (future use)
);
```

## Key Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Generate Key                                             │
│    - Admin clicks "Generate Key"                            │
│    - Backend creates 64-char random key                     │
│    - Stores in DB with is_active=1                          │
│    - Returns key to admin                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Extension Installs                                       │
│    - User installs extension                                │
│    - Extension calls /api/activate                          │
│    - Receives and stores key locally                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Key Active & In Use                                      │
│    - User scans prompts                                     │
│    - Extension includes key in X-Activation-Key header      │
│    - Backend validates: is_active=1? YES → 200 OK           │
│    - last_used updated to current timestamp                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
          ┌─────────────────┴──────────────────┐
          │                                    │
    ┌─────▼─────────┐              ┌──────────▼─────┐
    │ Deactivate    │              │ Delete Key      │
    │ is_active=0   │              │ Removed from DB │
    │ (Reversible)  │              │ (Permanent)     │
    └─────┬─────────┘              └────────────────┘
          │
          └─────────────────┬──────────────────┐
                            │                  │
              ┌─────────────▼──┐      ┌────────▼──────┐
              │ Reactivate     │      │ Key Expired    │
              │ is_active=1    │      │ (if set)       │
              │ Resume usage   │      │ 401 Unauthorized
              └────────────────┘      └────────────────┘
```

## Usage Workflow

### For Admin (Dashboard)
```
1. Open Dashboard
2. Scroll to "🔑 Extension Activation Keys" section
3. Enter hostname (optional)
4. Click "+ Generate Key"
5. Copy key → Send to user
6. Monitor key status in table
7. Deactivate if suspicious
8. Reactivate when safe
9. Delete when no longer needed
```

### For User (Getting Extension)
```
1. Install extension from Store
2. Extension auto-requests activation key from /api/activate
3. Backend generates key
4. Extension stores encrypted key locally
5. Key automatically included in all requests
6. Admin can manage key from dashboard
```

## Security Features

✅ **Key Generation**
- 64-character cryptographically secure random key
- Unique per extension instance
- Stored in SQLite with encryption at rest (future)

✅ **Key Validation**
- Checked on every API request
- 401 Unauthorized if missing or invalid
- Deactivated keys are rejected immediately

✅ **Activity Tracking**
- last_used timestamp updated on each validation
- Allows detection of inactive/unused keys
- Audit trail for security analysis

✅ **Granular Control**
- Activate/deactivate without deletion
- Permanent deletion option for compromised keys
- Temporary suspension for investigation

## Test Results

All features verified ✅:
```
[Test 1] Generate key via admin panel: ✅ PASS
[Test 2] View all keys: ✅ PASS
[Test 3] Deactivate key: ✅ PASS
[Test 4] Deactivated key rejected: ✅ PASS (401)
[Test 5] Reactivate key: ✅ PASS
[Test 6] Reactivated key works: ✅ PASS
```

## Future Enhancements

- [ ] Key expiration enforcement
- [ ] Bulk operations (deactivate multiple keys)
- [ ] Export keys to CSV
- [ ] Search/filter keys by hostname or extension_id
- [ ] Usage analytics (requests per key)
- [ ] Rate limiting per key
- [ ] Key rotation automation
- [ ] Email notifications on suspicious activity
