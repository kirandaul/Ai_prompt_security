# 🔐 Extension Activation & Authentication System

## Overview
Complete end-to-end extension authentication system to prevent unauthorized API access. Only legitimate, activated extensions can scan prompts.

## Architecture

### Backend (server.py + storage.py)

#### 1. Activation Key Generation (`/api/activate`)
- **Endpoint**: `POST /api/activate`
- **Request**: 
  ```json
  {
    "hostname": "hackathon-066",
    "user_agent": "Mozilla/5.0..."
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "activation_key": "4900f666e5209be46428cc997a361f4e...",
    "extension_id": "hackathon-066-a52deb10",
    "created_at": "2026-08-01T04:44:23+00:00"
  }
  ```

#### 2. Database Schema (`activation_keys` table)
```sql
CREATE TABLE activation_keys (
    id              INTEGER PRIMARY KEY,
    created_at      TEXT NOT NULL,
    key             TEXT UNIQUE NOT NULL,
    extension_id    TEXT NOT NULL,
    hostname        TEXT,
    user_agent      TEXT,
    is_active       INTEGER DEFAULT 1,
    last_used       TEXT,
    expires_at      TEXT
);
```

#### 3. Key Validation Middleware
- **Function**: `verify_activation_key(request)` (dependency)
- **Header**: `X-Activation-Key: <key>`
- **Applied to**:
  - `/api/scan` (text scanning)
  - `/api/scan-image` (image scanning)
  - `/api/scan-document` (document scanning)
- **Response on Missing Key**: `401 Unauthorized`
- **Response on Invalid Key**: `401 Unauthorized`

#### 4. Storage Functions
- `generate_activation_key(extension_id, hostname, user_agent)` → Returns unique key
- `validate_activation_key(key)` → Returns key info if valid, updates last_used
- `deactivate_key(key)` → Marks key as inactive
- `get_keys_by_extension(extension_id)` → Lists all keys for extension

### Extension (Chrome/Manifest)

#### 1. Activation on First Install (`activator.js`)
- **Trigger**: When extension loads
- **Flow**:
  1. Check if activation key exists in `chrome.storage.local`
  2. If not found, request key from `/api/activate`
  3. Encrypt key using XOR + Base64
  4. Store in `chrome.storage.local` under `psg_activation_key`
  5. Show success notification
- **Storage Keys**:
  - `psg_activation_key` → Encrypted activation key
  - `psg_extension_id` → Unique extension ID

#### 2. Encryption/Decryption
- **Algorithm**: XOR cipher + Base64 encoding
- **Secret**: `"psg-extension-secret"` (static)
- **Security Note**: This is obfuscation, not cryptographic encryption
  - Prevents accidental exposure (logs, screenshots)
  - NOT suitable for protecting against determined attackers
  - For production, use proper encryption (e.g., TweetNaCl.js)

#### 3. Key Injection in Requests (`detection.js`)
- **RemoteDetectionProvider** class updated to:
  1. Accept `activationKey` in options
  2. Add `X-Activation-Key` header to all POST requests
  3. Include key with text, image, and document scans

#### 4. Key Retrieval (`content.js`)
- **On Page Load**:
  1. Retrieve encrypted key from `chrome.storage.local`
  2. Decrypt using XOR cipher
  3. Pass to detection engine as `activationKey`
  4. Engine includes key in all API requests

## Request Flow

### First Install (Activation)
```
1. Extension loads (manifest.json loads activator.js first)
2. activator.js checks: Has key? NO
3. Calls POST /api/activate { hostname, user_agent }
4. Backend generates unique 64-char hex key
5. Stores in DB: activation_keys table
6. Returns key to extension
7. Extension encrypts and stores in chrome.storage.local
8. Shows "✅ Extension activated successfully"
```

### Subsequent API Requests
```
1. User types prompt in ChatGPT
2. content.js detects input
3. Retrieves encrypted key from storage
4. Decrypts key
5. Calls POST /api/scan with header: X-Activation-Key: <key>
6. Backend middleware verify_activation_key() checks:
   - Key exists in header? YES
   - Key valid in DB? YES
   - Key is_active? YES
7. Request processed normally
8. Response returned to extension
```

### Invalid Key Request
```
1. Request POST /api/scan without X-Activation-Key header
2. Backend returns: 401 Unauthorized
   "Missing activation key. Include 'X-Activation-Key' header."
3. Extension falls back to local rules (graceful degradation)
```

## Security Features

### ✅ Implemented
- Unique key per extension instance (extension_id)
- Key stored encrypted in browser storage
- Key validation on every request
- Key deactivation support
- Last-used timestamp tracking
- XOR obfuscation (prevents accidental exposure)
- Graceful fallback to local detection if key invalid

### ⚠️  Limitations & TODO
- **Encryption**: XOR is obfuscation, not true encryption
  - **Improvement**: Use TweetNaCl.js or libsodium for real encryption
- **Key Expiration**: Not enforced (see `expires_at` column)
  - **Improvement**: Add TTL validation in middleware
- **Key Rotation**: Not implemented
  - **Improvement**: Add key rotation endpoint + automatic refresh
- **Revocation**: Keys marked inactive but not removed
  - **Improvement**: Add admin panel for key management

## Testing

### Run End-to-End Tests
```bash
cd backend
python test_activation_flow.py
```

### Test Results (Verified ✅)
- Test 1: ✅ Activation key generation (200 OK)
- Test 2: ✅ Reject requests without key (401)
- Test 3: ✅ Accept requests with valid key (200)
- Test 4: ✅ Reject requests with invalid key (401)
- Test 5: ✅ Image scanning with valid key
- Test 6: ✅ Document scanning with valid key

## Files Modified/Created

### Backend
- `backend/storage.py` ← Added `activation_keys` table + functions
- `backend/server.py` ← Added `/api/activate`, `verify_activation_key()` middleware
- `backend/test_activation_flow.py` ← Comprehensive test suite

### Extension
- `extension/js/activator.js` ← NEW: Activation manager
- `extension/manifest.json` ← Updated: Load activator first
- `extension/detection.js` ← Updated: Include key in headers
- `extension/content.js` ← Updated: Retrieve and decrypt key

## Deployment Checklist

- [ ] Database migrated (schema updates applied)
- [ ] Backend restarted (server.py reloaded)
- [ ] Extension updated with new files
- [ ] First user installs extension
  - Extension calls `/api/activate`
  - Backend generates key
  - Extension stores key locally
- [ ] User opens ChatGPT
  - extension/content.js loads
  - Retrieves key from storage
  - Includes in all API requests
  - Backend validates key
- [ ] Verification: Scan works with key, fails without key

## Future Enhancements

1. **Key Rotation**: Automatic key refresh every 30 days
2. **Real Encryption**: TweetNaCl.js for true encryption
3. **Admin Dashboard**: Manage activation keys, view usage stats
4. **Key Expiration**: Auto-deactivate keys after expiry
5. **Rate Limiting**: Per-key request rate limits
6. **Audit Logging**: Track all key validation attempts
7. **Two-Factor Activation**: Require email verification
8. **Team Management**: Share keys across team members securely
