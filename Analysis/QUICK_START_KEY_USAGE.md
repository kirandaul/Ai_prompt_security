# 🚀 Quick Start: API Key Usage Tracking

## What It Does

When you generate an API key and share it with multiple people, you can now see **exactly which people/devices used that key** and **how many times each used it**.

---

## How to Use (3 Steps)

### Step 1: Generate a Key
```
Dashboard → "🔑 Extension Activation Keys"
Click "+ Generate Key"
Copy the key
Share it with your team
```

### Step 2: Users Use the Key
```
Extension loads → Users enter the key
All their scans are tagged with that key
Backend logs "User X on hostname Y used key Z"
```

### Step 3: Check Usage
```
Dashboard → "🔑 Extension Activation Keys"
Find the key you shared
Click "📊 Usage" button
See all hostnames that used it with count
```

---

## Example

```
You generate: key_A

You share with:
├─ Alice (my-laptop)
├─ Bob (office-pc)
└─ Charlie (home-desktop)

They all scan documents using key_A

You click "📊 Usage" on key_A

Popup shows:
├─ my-laptop: 23 scans
├─ office-pc: 15 scans
└─ home-desktop: 8 scans
```

---

## The Popup Shows

```
📊 Key Usage
├─ Key: a1b2c3...xyz
├─ Total Requests: 46
├─ First Used: 2026-08-01 10:30
├─ Last Used: 2026-08-01 16:45
│
├─ Devices:
│  ├─ my-laptop (23) - Last: 16:45
│  ├─ office-pc (15) - Last: 15:20
│  └─ home-desktop (8) - Last: 14:10
```

---

## What Changed

✅ Each scan now records **which key was used**  
✅ Backend endpoint `/api/admin/key-usage/{key}` shows **all hostnames that used it**  
✅ Dashboard button "📊 Usage" calls this endpoint  
✅ Popup displays the results  

---

## Perfect For

- 🔐 **Audit Trail:** Know exactly who used each key
- 🚨 **Security:** Detect if key was shared with unauthorized people
- 📊 **Reporting:** See usage statistics per key
- 🕵️ **Troubleshooting:** Figure out which device caused an issue

---

## Technical Details (Backend Devs)

**Database:** Each scan stored with `activation_key` column  
**Query:** `SELECT hostname, COUNT(*) FROM scans WHERE activation_key = ? GROUP BY hostname`  
**Endpoint:** `GET /api/admin/key-usage/{key}` (admin-only)  
**Response:** JSON with total requests and hostname breakdown  

---

## That's It!

Generate key → Share key → Click Usage → See who used it! 🎉
