#!/usr/bin/env python3
"""
Sync leads with emails to Google Sheets
"""

import sqlite3
import sys
sys.path.append('/Users/jonsmith/leadforge-scraper')

from google_sheets_integration import GoogleSheetsClient

def sync_leads_with_emails():
    """Sync all leads that have emails to Google Sheets"""

    print("=" * 60)
    print("🔄 Syncing Leads with Emails to Google Sheets")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()

    # Get all leads with emails
    cursor.execute('''
        SELECT id, business_name, industry, location, phone, website,
               rating, reviews_count, address, email, score, status
        FROM leads
        WHERE email IS NOT NULL
        AND email != ''
        ORDER BY score DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\n❌ No leads with emails found in database")
        return

    print(f"\n📊 Found {len(rows)} leads with email addresses")
    print("=" * 60)

    # Convert to lead format
    leads = []
    for row in rows:
        lead = {
            'id': row[0],
            'business_name': row[1],
            'industry': row[2],
            'location': row[3],
            'phone': row[4],
            'website': row[5],
            'rating': row[6],
            'reviews_count': row[7],
            'address': row[8],
            'email': row[9],
            'score': row[10],
            'status': row[11],
            'source': 'Email Discovery'
        }
        leads.append(lead)

    try:
        # Connect to Google Sheets
        print("\n🔗 Connecting to Google Sheets...")
        client = GoogleSheetsClient()

        # Add leads to sheet
        print(f"📝 Syncing {len(leads)} leads to Google Sheets...")
        synced = client.add_leads_to_sheet(leads)

        print("=" * 60)
        print(f"\n✅ Successfully synced {synced} leads to Google Sheets!")
        print("=" * 60)

        print("\n📋 Synced Leads:")
        for i, lead in enumerate(leads[:10], 1):
            print(f"   {i}. {lead['business_name']}")
            print(f"      Email: {lead['email']}")
            print(f"      Score: {lead['score']}")

        if len(leads) > 10:
            print(f"   ... and {len(leads) - 10} more")

        print("\n" + "=" * 60)
        print("✅ Sync Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sync_leads_with_emails()
