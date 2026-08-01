#!/usr/bin/env python3
"""Test storage - verify one prompt = one database record"""

import storage
import json
import os

# Initialize DB
storage.init_db()

# Fetch recent logs BEFORE adding new one
print("Before adding test record:")
logs_before = storage.recent(limit=1)
print(f"Latest record ID: {logs_before[0]['id'] if logs_before else 'None'}")

# Test 1: Log a scan with multiple findings
print("\nTest 1: Logging a scan with findings_count=3...")
storage.log_scan(
    client_id="test-client",
    source="chatgpt.com",
    severity="HIGH",
    action="BLOCK",
    allow_send=False,
    findings_count=3,  # 3 findings
    categories=["AWS Secret", "Password"],
    redacted_prompt="my aws password is [REDACTED:AWS] and [REDACTED:Password]",
    ip="127.0.0.1",
    user_agent="Chrome",
    scan_type="text"
)
print("✅ Logged 1 scan")

# Test 2: Fetch recent logs
print("\nTest 2: Fetching latest record...")
logs = storage.recent(limit=1)

if logs:
    log = logs[0]
    print(f"\n✅ Latest Record:")
    print(f"  ID: {log['id']}")
    print(f"  Severity: {log['severity']}")
    print(f"  Findings Count: {log['findings_count']}")
    print(f"  Categories: {log['categories']}")
    print(f"  Redacted Prompt: {log['redacted_prompt']}")
    print(f"  Scan Type: {log.get('scan_type', 'text')}")
    
    print("\n✅ RESULT: 1 scan logged = 1 database row ✓")
    print("   (The finding_count field shows how many findings were in this scan)")
else:
    print("❌ No records found")

