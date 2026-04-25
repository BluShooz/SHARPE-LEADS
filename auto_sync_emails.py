#!/usr/bin/env python3
"""
Auto-Sync Discovered Emails to Google Sheets
Automatically syncs after email discovery
"""

import requests
import time
import sqlite3
import os
from datetime import datetime

API_BASE = "http://localhost:8000"
DB_PATH = 'leads.db'

def check_for_new_emails():
    """Check if there are new emails to sync"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM leads
        WHERE email IS NOT NULL
        AND email != ''
    ''')
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def trigger_sync():
    """Trigger sync to Google Sheets via API"""
    try:
        response = requests.post(
            f"{API_BASE}/api/sync-to-sheets",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False), result
        else:
            return False, {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def main():
    print("=" * 60)
    print("🔄 Auto-Sync Emails to Google Sheets")
    print("=" * 60)
    
    # Check for emails
    email_count = check_for_new_emails()
    print(f"\n📊 Found {email_count} leads with emails in database")
    
    if email_count == 0:
        print("❌ No emails to sync")
        return
    
    # Trigger sync
    print("\n🔄 Triggering sync to Google Sheets...")
    success, result = trigger_sync()
    
    if success:
        synced = result.get('synced', 0)
        print(f"\n✅ Sync complete!")
        print(f"   Emails synced: {synced}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
    else:
        print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
