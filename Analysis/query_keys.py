#!/usr/bin/env python3
import sqlite3
import os

# Get absolute path
db_path = r"c:\Users\kirandau\Desktop\AI-promt\backend\psg_logs.db"

print(f"Database path: {db_path}")
print(f"Exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("❌ Database file not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check activation_keys table
    cursor.execute("SELECT COUNT(*) as count FROM activation_keys")
    count = cursor.fetchone()['count']
    
    print(f"\n✅ Database opened successfully")
    print(f"✅ Total activation keys: {count}\n")
    
    if count > 0:
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
            LIMIT 10
        """)
        
        keys = cursor.fetchall()
        print(f"Showing {len(keys)} keys:\n")
        for i, row in enumerate(keys, 1):
            status = "🟢 ACTIVE" if row['is_active'] else "🔴 INACTIVE"
            key_short = row['key'][:16] + "..." + row['key'][-4:]
            print(f"{i}. {status}")
            print(f"   Key: {key_short}")
            print(f"   Ext ID: {row['extension_id']}")
            print(f"   Hostname: {row['hostname']}")
            print(f"   Created: {row['created_at']}")
            print()
    else:
        print("⚠️  No keys in database")
        print("\nTo generate a key:")
        print("  POST http://127.0.0.1:3000/api/admin/generate-key")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
