#!/usr/bin/env python3
"""
Test Google Sheets reading with debug output
"""

import sys
sys.path.append('/Users/jonsmith/leadforge-scraper')

from google_sheets_integration import GoogleSheetsClient

print("🔍 Testing Google Sheets Connection...")
print("=" * 60)

try:
    client = GoogleSheetsClient()
    leads = client.read_all_leads()

    print(f"\n✅ Total leads read: {len(leads)}")
    print("=" * 60)

    if len(leads) > 0:
        print("\n📋 Sample leads (first 5):")
        for i, lead in enumerate(leads[:5], 1):
            print(f"\n{i}. {lead.get('business_name', 'Unknown')}")
            print(f"   Phone: {lead.get('phone', 'N/A')}")
            print(f"   Email: {lead.get('email', 'N/A')}")
            print(f"   Website: {lead.get('website', 'N/A')}")
            print(f"   Location: {lead.get('location', 'N/A')}")
    else:
        print("\n❌ No leads found!")
        print("\n🔍 Debugging...")

        # Try to access the worksheet directly
        import gspread
        from google.oauth2.service_account import Credentials

        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key("1F-joQOczNCb2JGVgKx0w3GompkJtzzcLEd6QTVn0qgo")
        worksheet = sheet.worksheet("All Leads")

        # Get all data
        all_data = worksheet.get_all_records()
        print(f"\n   Total rows found: {len(all_data)}")

        if len(all_data) > 0:
            print(f"\n   First row keys: {list(all_data[0].keys())[:10]}")
            print(f"\n   Sample row data:")
            for key, value in list(all_data[0].items())[:5]:
                print(f"      {key}: {value}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
