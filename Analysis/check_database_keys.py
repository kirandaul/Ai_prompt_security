#!/usr/bin/env python3
"""
Check what keys are in the database
"""

import sqlite3
import os

db_path = "backend/psg.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    print("   The database hasn't been created yet.")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='activation_keys'
    """)
    
    if not cursor.fetchone():
        print("❌ activation_keys table does not exist")
        exit(1)
    
    # Get all keys
    cursor.execute("""
        SELECT 
            key,
            extension_id,
            hostname,
            is_active,
            created_at,
            last_used
        FROM activation_keys
        ORDER BY created_at DESC
    """)
    
    keys = cursor.fetchall()
    
    if not keys:
        print("⚠️  No keys in database")
        print("\nTo generate a key, run:")
        print("  curl -X POST http://127.0.0.1:3000/api/admin/generate-key")
        exit(0)
    
    print(f"✅ Found {len(keys)} activation key(s) in database\n")
    
    for i, row in enumerate(keys, 1):
        status = "🟢 ACTIVE" if row['is_active'] else "🔴 INACTIVE"
        print(f"{i}. {status}")
        print(f"   Key: {row['key'][:16]}...{row['key'][-4:]}")
        print(f"   Ext: {row['extension_id']}")
        print(f"   Host: {row['hostname']}")
        print(f"   Created: {row['created_at']}")
        print(f"   Last Used: {row['last_used'] or '—'}")
        print()
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error reading database: {e}")
    exit(1)
