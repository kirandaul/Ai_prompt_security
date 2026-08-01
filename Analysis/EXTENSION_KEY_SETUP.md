# 🔑 Extension Key Setup - User Flow

## Overview
New process for setting up extension with activation key:

1. **Admin generates key** in dashboard
2. **Admin copies key** with one click
3. **User installs extension**
4. **Key input dialog appears** (blocks extension until key entered)
5. **User pastes key**
6. **Extension activates** and becomes usable

## Admin Dashboard - Generate & Copy Key

### Step 1: Generate Key
```
1. Open http://localhost:3000
2. Login with admin credentials
3. Scroll to "🔑 Extension Activation Keys" panel
4. (Optional) Enter hostname (e.g., "hackathon-066")
5. Click "+ Generate Key"
```

### Step 2: Auto-Copy & Share
```
✅ Key is AUTOMATICALLY COPIED to clipboard
✅ Alert shows: "Key: d1c94ecced8113190ac483573c489cc8..."
✅ Extension ID: admin-881b42f7

Share the 64-character key with user
```

### Step 3: View in Table
```
Key appears in table with:
- Status: 🟢 Active
- Key (clickable to copy again)
- Extension ID
- Hostname
- Created timestamp
- Last Used (—initially)
```

## User Installation - Key Input Dialog

### Step 1: Install Extension
```
1. User installs extension from Chrome Web Store
2. Extension loads in browser
3. Extension checks: "Do I have a key stored?"
   → NO → Show key input dialog
   → YES → Continue normally
```

### Step 2: Key Input Dialog
```
┌─────────────────────────────────────┐
│             🔐                      │
│        Activate Extension           │
│                                     │
│  Enter your activation key to       │
│  enable the extension               │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Activation Key                  │ │
│ │ [Paste 64-char key here...    ] │ │
│ │ ☐ Show key                      │ │
│ │                                 │ │
│ │ [🔓 Activate]                   │ │
│ │                                 │ │
│ │ Don't have a key?               │ │
│ │ Contact administrator:          │ │
│ │ http://localhost:3000           │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Step 3: User Enters Key
```
1. User receives key from admin
2. User opens extension
3. Dialog appears automatically
4. User pastes 64-character key
5. (Optional) Click "Show key" to verify
6. Click "🔓 Activate" or press Enter
```

### Step 4: Validation
```
Key format validation:
✅ Exactly 64 characters
✅ Only hexadecimal (0-9, a-f)
✅ No spaces or special characters

❌ Invalid format → Error message shown
❌ Less than 64 chars → Rejected
❌ Non-hex characters → Rejected
```

### Step 5: Key Stored
```
1. Key is validated
2. Key is ENCRYPTED (XOR + Base64)
3. Stored in chrome.storage.local
4. ✅ Success message shown
5. Page reloads automatically
6. Extension now works with key
```

### Step 6: Extension Ready
```
After reload:
✅ activator.js checks: Key exists? YES
✅ Initializes normally
✅ All features available:
   - Text detection
   - Image detection  
   - Document detection
   - Critical blocker
   - Document scanner
   - Debug logging
```

## Flow Diagram

```
┌─────────────────────────────────────┐
│ ADMIN DASHBOARD                     │
│ 1. Generate Key                     │
│ 2. ✅ Auto-copy to clipboard        │
│ 3. Share key to user                │
└─────────┬───────────────────────────┘
          │
          ↓ (User receives key)
┌─────────────────────────────────────┐
│ USER INSTALLATION                   │
│ 1. Install extension                │
│ 2. key-prompt.js checks: Key?       │
│    → NO: Show dialog                │
│ 3. User pastes key in dialog        │
│ 4. Validation: 64 hex chars? YES    │
│ 5. Encrypt & store in storage       │
│ 6. Page reloads                     │
│ 7. activator.js checks: Key?        │
│    → YES: Continue normally         │
│ 8. ✅ Extension active!             │
└─────────────────────────────────────┘
```

## Extension Loading Sequence

```
1. Page loads (run_at: document_start)
   ↓
2. key-prompt.js (FIRST)
   → Check: Key in storage?
   → NO: Show input dialog
   → Wait for user input
   ↓
3. activator.js (AFTER key-prompt.js)
   → Already has key in storage
   → Initialize normally
   ↓
4. critical_blocker.js
   → Setup critical severity blocking
   ↓
5. document_scanner.js
   → Setup document upload detection
   ↓
6. detection.js
   → Initialize detection engine
   ↓
7. content.js
   → Retrieve key from storage
   → Inject into detection engine
   → Ready to scan!
```

## Files Changed

### New Files
- `extension/js/key-prompt.js` - Key input dialog (LOADS FIRST)

### Updated Files
- `extension/manifest.json` - Added key-prompt.js first in content_scripts
- `dist/src/App.jsx` - Added copy button & auto-copy to dashboard

### Backend (Already Done)
- `backend/server.py` - /api/admin/* endpoints
- `backend/storage.py` - Key management functions

## Key Features

### Admin Panel
✅ **Generate Key** - Creates 64-char random key
✅ **Auto-Copy** - Key auto-copied to clipboard
✅ **View All** - Table shows all keys
✅ **Clickable Copy** - Click key in table to copy again
✅ **Activate/Deactivate** - Control key status
✅ **Delete** - Permanently remove key
✅ **Statistics** - Total/Active/Inactive count

### User Activation
✅ **Auto-Dialog** - Shows automatically if no key
✅ **Visual Design** - Clear, user-friendly interface
✅ **Password Toggle** - Show/hide key option
✅ **Validation** - Format checking before save
✅ **Error Messages** - Clear error feedback
✅ **Encryption** - Key encrypted in storage
✅ **Auto-Reload** - Reloads after activation

## Security

✅ Key in storage encrypted (XOR + Base64)
✅ Key validated on EVERY request
✅ Admin can deactivate/reactivate anytime
✅ 401 Unauthorized if key invalid
✅ Deactivated keys work immediately
✅ Reactivated keys work immediately

## Troubleshooting

### "Invalid key format"
```
Key must be:
- Exactly 64 characters
- Only 0-9 and a-f
- No spaces or special chars

Example valid: d1c94ecced8113190ac483573c489cc8...
```

### Key doesn't appear in dialog
```
1. Check key was copied from dashboard
2. Check for extra spaces
3. Try clicking "Show key" to verify
4. Contact admin if still failing
```

### Extension still doesn't work
```
1. Clear browser cache
2. Reinstall extension
3. Check key is active in admin panel (🟢)
4. Contact admin if deactivated
```

### Need to change key
```
1. Store new key in admin panel
2. Old key still works (can coexist)
3. Or deactivate old key
4. User uninstalls and reinstalls
5. On new install, provide new key
```
