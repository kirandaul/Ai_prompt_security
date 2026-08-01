# 🚀 Quick Test Guide - Complete System

## Prerequisites
- Backend running: `python -m uvicorn server:app --host 127.0.0.1 --port 3000 --reload`
- Chrome browser installed
- Extension not yet installed (or use incognito for fresh test)

---

## 🧪 Test 1: Automated Tests (2 minutes)

### Run End-to-End Activation Tests
```bash
cd c:\Users\kirandau\Desktop\AI-promt
python test_end_to_end.py
```

**Expected Output:**
```
✅ PASS: Generate Key
✅ PASS: Get All Keys
✅ PASS: Scan With Key
✅ PASS: Scan Without Key
✅ PASS: Deactivate Key
✅ PASS: Scan With Deactivated Key
✅ PASS: Reactivate Key
✅ PASS: Scan With Reactivated Key

🎉 ALL TESTS PASSED! 🎉
```

### Run Document Scanning Tests
```bash
python test_document_scanning.py
```

**Expected Output:**
```
✅ PASS: Document With Key
✅ PASS: Document Without Key

🎉 ALL DOCUMENT TESTS PASSED! 🎉
```

---

## 👤 Test 2: Admin Dashboard (3 minutes)

### Step 1: Open Dashboard
```
http://localhost:3000
```

### Step 2: Generate Key
```
1. Scroll to "🔑 Extension Activation Keys" section
2. (Optional) Enter hostname: "test-device-001"
3. Click "+ Generate Key"
4. ✅ Alert appears with generated key
5. ✅ Key auto-copied to clipboard
```

**Expected:**
- Key format: 64 hexadecimal characters
- Extension ID: admin-XXXXXXXX
- Success message appears

### Step 3: View Keys in Table
```
1. Refresh page (or already showing)
2. Look at key table
3. ✅ New key appears with status 🟢 Active
4. ✅ Click key to copy again (turns green with ✅ Copied!)
```

**Expected:**
- Status: 🟢 Active
- Created: Today's date
- Last Used: —
- Clickable copy functionality

### Step 4: Test Activate/Deactivate
```
1. Find your key in table
2. Click "🔴 Deactivate" button
3. ✅ Status changes to 🔴 Inactive
4. Click "🟢 Activate" button
5. ✅ Status changes back to 🟢 Active
```

**Expected:**
- Status toggles immediately
- No page refresh needed
- Table updates in real-time

### Step 5: Test Delete
```
1. (Optional) Create another key for deletion
2. Click "🗑 Delete" button
3. Confirm dialog: "Delete key ...?"
4. ✅ Key removed from table
```

**Expected:**
- Confirmation before deletion
- Key disappears from table
- Count updates

---

## 🔌 Test 3: Extension Installation (5 minutes)

### Step 1: Load Extension in Chrome
```
1. Open Chrome
2. Go to chrome://extensions/
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select: c:\Users\kirandau\Desktop\AI-promt\extension
6. ✅ Extension appears in list
```

**Expected:**
- Extension name: "Cybage Browser Prompt Detection"
- Version: 1.2.0
- Status: Enabled

### Step 2: Clear Storage (First-Time Setup)
```
In Chrome DevTools (F12):
1. Go to Applications tab
2. Storage → chrome.storage → local
3. ✅ No "psg_activation_key" yet
```

**Expected:**
- Storage is empty initially
- Ready for key input

### Step 3: Navigate to ChatGPT
```
1. Go to https://chatgpt.com (or Claude.ai)
2. Page starts to load
3. ✅ Key input dialog appears (before extension loads)
```

**Expected:**
- Beautiful modal dialog appears
- Title: "🔐 Activate Extension"
- Input field for 64-character key
- Show/Hide toggle
- "Contact administrator" message
- No extension functionality yet

### Step 4: Enter Activation Key
```
1. Get key from admin dashboard test (or run test_end_to_end.py)
2. Copy the 64-character key
3. Paste into dialog input field
4. (Optional) Click "Show key" checkbox to verify
5. Click "🔓 Activate" button (or press Enter)
```

**Expected:**
- Input accepts the key
- No error message
- Success message: "✅ Activation key saved! Reloading page..."
- Page reloads automatically

### Step 5: Extension Active
```
After reload:
1. ✅ Page fully loads
2. ✅ No error messages
3. ✅ Extension is working
```

Check in DevTools:
```
1. F12 → Console tab
2. Should see extension logs:
   - ✅ Detection engine initialized
   - ✅ Critical blocker active
   - ✅ Document scanner ready
```

---

## 💬 Test 4: Text Scanning (2 minutes)

### With Extension Active:

### Step 1: Try Safe Text
```
In ChatGPT input:
"Hello, how are you today?"

Press Tab+Enter (to bypass blocker if needed)
✅ Sends normally
✅ No popup
✅ No blocking
```

**Expected:**
- Normal submission
- No detection alerts
- Message sent

### Step 2: Try Sensitive Text
```
In ChatGPT input:
"My AWS key is AKIAIOSFODNN7EXAMPLE"

Press Enter
✅ Popup appears: "You can't submit"
❌ Enter key blocked
```

**Expected:**
- Popup overlay appears
- All Enter key variants blocked (Enter, Ctrl+Enter, Numpad Enter)
- "You can't submit" message
- Text is not sent

### Step 3: Try Credit Card
```
Clear previous text, try:
"My card number is 4532-1111-2222-3333"

Press Enter
✅ Popup appears
❌ Enter blocked
```

**Expected:**
- Immediate detection
- Blocking popup
- No submission

---

## 📄 Test 5: Document Scanning (2 minutes)

### Step 1: Create Test Document
```
Create a file: test-sensitive.txt

Content:
My AWS Key: AKIAIOSFODNN7EXAMPLE
Credit Card: 4532-1111-2222-3333
PAN: BTKPD9226K
Email: john.doe@company.com
```

### Step 2: Upload in ChatGPT
```
1. In ChatGPT, click file upload button
2. Select test-sensitive.txt
3. ✅ File sent to backend for scanning
4. ✅ Extension processes findings
5. ✅ Shows detection results
```

**Expected:**
- File uploads without error
- Backend scans document
- Multiple findings detected
- Extension shows detection summary

### Step 3: With Critical Findings
```
If findings are HIGH/CRITICAL:
✅ Popup appears
❌ Enter blocked
❌ Cannot submit
```

**Expected:**
- Critical severity blocks submission
- Clear error message
- User must delete/edit content

---

## 🔍 Test 6: Dashboard View (2 minutes)

### Step 1: Check Latest Scans
```
1. Go back to http://localhost:3000
2. Scroll to "📊 Recent Scans" section
3. ✅ Latest scans appear at top
```

**Expected:**
- Scans ordered newest first
- Most recent scans visible immediately
- Timestamp shown

### Step 2: View Scan Details
```
Latest scan should show:
- Type: text / image / document
- Severity: SAFE / LOW / MEDIUM / HIGH / CRITICAL
- Action: ALLOW / BLOCK
- Hostname: (your device name or extension)
- IP: (your IP address)
- Findings Count: (number of detections)
```

**Expected:**
- All fields populated
- Hostname and IP visible
- Correct scan type
- Accurate severity

### Step 3: Filter by Type
```
1. Find "Filter by Type" dropdown
2. Select: "document"
3. ✅ Shows only document scans
4. Select: "text"
5. ✅ Shows only text scans
6. Select: "All Types"
7. ✅ Shows all scans
```

**Expected:**
- Filtering works immediately
- Table updates without reload
- Count matches selection

---

## ✅ Final Verification Checklist

### Backend ✅
- [ ] Backend running (port 3000)
- [ ] No error messages in terminal
- [ ] Database responding to requests

### Admin Dashboard ✅
- [ ] Dashboard loads (http://localhost:3000)
- [ ] Can generate keys
- [ ] Auto-copy works (try pasting)
- [ ] Copy button in table works
- [ ] Can activate/deactivate keys
- [ ] Can delete keys
- [ ] Statistics show correct count

### Extension ✅
- [ ] Extension loads in Chrome
- [ ] Key prompt dialog appears
- [ ] Can enter 64-character key
- [ ] Show/Hide toggle works
- [ ] Activation succeeds
- [ ] No console errors

### Scanning ✅
- [ ] Text detection works
- [ ] Image detection works
- [ ] Document detection works
- [ ] Critical blocker blocks submission
- [ ] Popup appears for HIGH/CRITICAL
- [ ] All 21 detectors working

### Dashboard Logging ✅
- [ ] Scans appear in dashboard
- [ ] Latest scans first
- [ ] Scan type shown (text/image/document)
- [ ] Hostname displayed
- [ ] IP displayed
- [ ] Severity correct

### Security ✅
- [ ] 401 without key
- [ ] 401 with deactivated key
- [ ] Works with activated key
- [ ] Deactivation blocks immediately
- [ ] Reactivation works immediately

---

## 🐛 Troubleshooting

### "Invalid key format" in Dialog
```
Solution:
✓ Key must be exactly 64 characters
✓ Only 0-9 and a-f (hexadecimal)
✓ No spaces, hyphens, or special chars
✓ Check you copied full key

Try again with correct key
```

### Extension doesn't load
```
Solution:
✓ Check extension folder path is correct
✓ Check manifest.json exists
✓ Check file permissions
✓ Try: chrome://extensions/ → remove → load unpacked again
```

### Backend not responding
```
Solution:
✓ Check terminal: "python -m uvicorn server:app --host 127.0.0.1 --port 3000 --reload"
✓ Check port 3000 not in use: netstat -ano | findstr :3000
✓ Kill process if stuck: taskkill /PID <PID> /F
✓ Restart backend
```

### Key doesn't appear in dashboard
```
Solution:
✓ Refresh dashboard page
✓ Check browser console for errors (F12)
✓ Check backend logs for errors
✓ Try generating new key
```

### Scans not showing in dashboard
```
Solution:
✓ Try scanning with sensitive text again
✓ Refresh dashboard
✓ Check if severity=SAFE (those don't store)
✓ Check database: backend terminal should show inserts
```

---

## 📈 Success Criteria

### All Tests Pass If:
1. ✅ Backend starts without errors
2. ✅ test_end_to_end.py shows 8/8 PASSED
3. ✅ test_document_scanning.py shows 2/2 PASSED
4. ✅ Dashboard generates and copies keys
5. ✅ Extension loads and asks for key
6. ✅ Key input dialog works and validates
7. ✅ Text scanning detects sensitive info
8. ✅ Document scanning works
9. ✅ Critical blocker blocks HIGH/CRITICAL
10. ✅ Dashboard shows all scans with details

---

## 🎉 You're Done!

If all above tests pass, the complete system is operational:

✅ Extension authentication system
✅ Admin key management
✅ Critical blocker
✅ Document scanning
✅ Dashboard logging
✅ All 21 detectors

**System is ready for production use!**

---

*Estimated Total Test Time: 15-20 minutes*
*All tests should pass completely*
